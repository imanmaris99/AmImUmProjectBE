from decimal import Decimal
from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.order_model import OrderModel
from app.models.shipment_model import ShipmentModel
from app.models.order_item_model import OrderItemModel
from app.dtos import order_dtos

import json
import logging

from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import redis_client, custom_json_serializer

logger = logging.getLogger(__name__)

CACHE_TTL = 3600
RESPONSE_MESSAGE = "All orders accessed successfully"

def my_order(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 100
    ) -> Result[order_dtos.GetOrderInfoResponseDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"orders:{user_id}:{skip}:{limit}"

        # Check if wishlist data exists in Redis
        cached_order = None
        if redis_client:
            try:
                cached_order = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read order list cache for key %s: %s", redis_key, cache_error)
        if cached_order:
            # Data is found in cache, return it
            order_data = json.loads(cached_order)
            return build(data=order_dtos.GetOrderInfoResponseDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=order_data['data']
            ))
        
        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        order_models = db.execute(
            select(OrderModel)
            .options(
                selectinload(OrderModel.user),
                selectinload(OrderModel.shipments).selectinload(ShipmentModel.shipment_address),
                selectinload(OrderModel.shipments).selectinload(ShipmentModel.courier),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.products),
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.pack_type),
            )
            .where(OrderModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not order_models:
            return build(data=order_dtos.GetOrderInfoResponseDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=[]
            ))

        order_dto = [
            order_dtos.GetOrderInfoDto(
                id=order.id,
                status=order.status,
                total_price=order.total_price,
                shipment_id=order.shipment_id,
                delivery_type=order.delivery_type,
                notes=order.notes,
                customer_name=order.customer_name,
                created_at=order.created_at,
                shipping_cost=order.shipping_cost,
                order_item_lists=order.order_item_lists
            )
            for order in order_models
        ]

        # Save the result to Redis cache
        cache_data = {
            'data': [wish.model_dump() for wish in order_dto]
        }

        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(cache_data, default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write order list cache for key %s: %s", redis_key, cache_error)

        # Return DTO dengan respons yang telah dibangun
        return build(data=order_dtos.GetOrderInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            data=order_dto,
        ))
    
    except (IntegrityError, DataError) as db_error:
        return build(error=handle_db_error(db, db_error))

    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi HTTPException
        return build(error=http_ex)
    
    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))
from decimal import Decimal
from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.order_model import OrderModel
from app.dtos import order_dtos

import json

from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600

def detail_order(
        db: Session, 
        user_id: str,  
        order_id: str
    ) -> Result[order_dtos.GetOrderDetailResponseDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"order:{user_id}:{order_id}"

        # Check if product data exists in Redis
        cached_order = redis_client.get(redis_key)
        if cached_order:
            order_detail_dto = order_dtos.GetOrderDetailDto(**json.loads(cached_order))
            return build(data=order_dtos.GetOrderDetailResponseDto(
                status_code=200,
                message=f"Order details for order ID {order_id} accessed successfully. (from cache)",
                data=order_detail_dto
            ))
        
        # Query untuk mengambil order berdasarkan user_id dan order_id
        order = db.execute(
            select(OrderModel)
            .where(
                OrderModel.id == order_id,
                OrderModel.customer_id == user_id
            )
        ).scalars().first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Order with ID {order_id} for user ID {user_id} not found."
                ).dict()
            )

        # Format data order ke dalam DTO
        order_detail_dto = order_dtos.GetOrderDetailDto(
            id=order.id,
            status=order.status,
            total_price=order.total_price,
            delivery_type=order.delivery_type,
            notes=order.notes,
            customer_name=order.customer_name,
            created_at=order.created_at,
            shipping_cost=order.shipping_cost,
            my_shipping=order.my_shipping,
            order_item_lists=order.order_item_lists
        )

        # Cache the result in Redis
        redis_client.setex(redis_key, CACHE_TTL, json.dumps(order_detail_dto.dict(), default=custom_json_serializer))

        # Return DTO dengan respons yang telah dibangun
        return build(data=order_dtos.GetOrderDetailResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Order details for order ID {order_id} accessed successfully.",
            data=order_detail_dto,
        ))
    
    except (IntegrityError, DataError) as db_error:
        raise handle_db_error(db, db_error)
    
    except HTTPException as http_ex:
        db.rollback()
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



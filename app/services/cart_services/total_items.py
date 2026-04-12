from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos

import json
import logging

from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.services.cart_services.support_function import get_total_records

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 3600
RESPONSE_MESSAGE = "Total cart items retrieved successfully"

def total_items(
        db: Session, 
        user_id: str
    ) -> Result[cart_dtos.AllItemNotificationDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"carts:{user_id}"

        # Check if product data exists in Redis
        cached_user = None
        if redis_client:
            try:
                cached_user = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read cart total cache for key %s: %s", redis_key, cache_error)
        if cached_user:
            total_notifications = cart_dtos.TotalItemNotificationDto(**json.loads(cached_user))
            return build(data=cart_dtos.AllItemNotificationDto(
                status_code=200,
                message=RESPONSE_MESSAGE,
                data=total_notifications
            ))

        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        cart_items = db.execute(
            select(CartProductModel)
            .where(CartProductModel.customer_id == user_id)
        ).scalars().all()

        if not cart_items:
            return build(data=cart_dtos.AllItemNotificationDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=cart_dtos.TotalItemNotificationDto(total_items=0)
            ))

        # Hitung total_records
        total_records = get_total_records(db, user_id)

        total_notifications=cart_dtos.TotalItemNotificationDto(
            total_items=total_records
        )

        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(total_notifications.dict(), default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write cart total cache for key %s: %s", redis_key, cache_error)

        # Return DTO dengan respons yang telah dibangun
        return build(data=cart_dtos.AllItemNotificationDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            data=total_notifications
        ))
    
    except (IntegrityError, DataError) as db_error:
        db.rollback()
        error_type = "Conflict" if isinstance(db_error, IntegrityError) else "Unprocessable Entity"
        status_code = status.HTTP_409_CONFLICT if isinstance(db_error, IntegrityError) else status.HTTP_422_UNPROCESSABLE_ENTITY
        return build(error=HTTPException(
            status_code=status_code,
            detail=ErrorResponseDto(
                status_code=status_code,
                error=error_type,
                message=f"Database error: {str(db_error)}"
            ).dict()
        ))
    
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
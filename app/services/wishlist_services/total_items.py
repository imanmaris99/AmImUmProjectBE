from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

import json
import logging

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.wishlist_services.support_function import get_total_records, handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 3600 
RESPONSE_MESSAGE = "Wishlist total items retrieved successfully"


def total_items(
        db: Session, 
        user_id: str
    ) -> Result[wishlist_dtos.AllItemNotificationDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"wishlists:{user_id}"

        # Check if address data exists in Redis
        cached_wish = None
        if redis_client:
            try:
                cached_wish = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read wishlist total cache for key %s: %s", redis_key, cache_error)
        if cached_wish:
            quantity_items = wishlist_dtos.TotalItemWishlistDto (**json.loads(cached_wish))

            return build(data=wishlist_dtos.AllItemNotificationDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=quantity_items
            ))

        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        wishlist_items = db.execute(
            select(WishlistModel)
            .where(WishlistModel.customer_id == user_id)

        ).scalars().all()

        if not wishlist_items:
            quantity_items = wishlist_dtos.TotalItemWishlistDto(total_items=0)
            return build(data=wishlist_dtos.AllItemNotificationDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=quantity_items
            ))

        # Hitung total_records
        total_records = get_total_records(db, user_id)

        quantity_items = wishlist_dtos.TotalItemWishlistDto(
            total_items=total_records
        )

        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(quantity_items.dict()))
            except Exception as cache_error:
                logger.warning("Failed to write wishlist total cache for key %s: %s", redis_key, cache_error)

        # Return DTO dengan respons yang telah dibangun
        return build(data=wishlist_dtos.AllItemNotificationDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            data=quantity_items
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
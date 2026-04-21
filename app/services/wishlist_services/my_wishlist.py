from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.utils.result import build, Result

import json
import logging

from app.libs.redis_config import custom_json_serializer, redis_client  # Redis client

logger = logging.getLogger(__name__)

CACHE_TTL = 300
RESPONSE_MESSAGE = "Wishlist accessed successfully"

def my_wishlist(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 100
    ) -> Result[wishlist_dtos.AllWishlistResponseCreateDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"wishlist:{user_id}:{skip}:{limit}"

        # Check if wishlist data exists in Redis
        cached_wishlist = None
        if redis_client:
            try:
                cached_wishlist = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read wishlist cache for key %s: %s", redis_key, cache_error)
        if cached_wishlist:
            # Data is found in cache, return it
            wishlist_data = json.loads(cached_wishlist)
            return build(data=wishlist_dtos.AllWishlistResponseCreateDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                total_records=wishlist_data['total_records'],
                data=wishlist_data['data']
            ))

        # Query untuk mengambil wishlist berdasarkan user_id dengan pagination
        wishlist_model = db.execute(
            select(WishlistModel)
            .where(WishlistModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not wishlist_model:
            return build(data=wishlist_dtos.AllWishlistResponseCreateDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                total_records=0,
                data=[]
            ))

        # Hitung total_records
        total_records = db.execute(
            select(func.count())
            .select_from(WishlistModel)
            .where(
                WishlistModel.customer_id == user_id
            )
        ).scalar()

        # Konversi wishlist menjadi DTO
        wishlist_dto = [
            wishlist_dtos.WishlistInfoCreateDto(
                id=wish.id,
                product_name=wish.product_name,
                product_variant=wish.product_variant,
                created_at=wish.created_at
            )
            for wish in wishlist_model
        ]

        # Save the result to Redis cache
        cache_data = {
            'total_records': total_records,
            'data': [wish.model_dump() for wish in wishlist_dto]
        }
        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(cache_data, default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write wishlist cache for key %s: %s", redis_key, cache_error)

        # Return DTO with success message
        return build(data=wishlist_dtos.AllWishlistResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            total_records=total_records,
            data=wishlist_dto
        ))

    except IntegrityError as ie:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database integrity error: {str(ie)}"
            ).dict()
        ))

    except DataError as de:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error="Unprocessable Entity",
                message=f"Data error: {str(de)}"
            ).dict()
        ))

    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))
    
    except HTTPException as http_ex:
        return build(error=http_ex)
    
    except (ValueError, TypeError) as te:
        return build(error=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error="Unprocessable Entity",
                message=f"Invalid input: {str(te)}"
            ).dict()
        ))
    
    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))

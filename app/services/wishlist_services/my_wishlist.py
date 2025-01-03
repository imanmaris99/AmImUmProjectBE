from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from typing import List, Type

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.utils.result import build, Result

import json
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client  # Redis client

CACHE_TTL = 300

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
        cached_wishlist = redis_client.get(redis_key)
        if cached_wishlist:
            # Data is found in cache, return it
            wishlist_data = json.loads(cached_wishlist)
            return build(data=wishlist_dtos.AllWishlistResponseCreateDto(
                status_code=status.HTTP_200_OK,
                message=f"All products wishlist for user ID {user_id} accessed successfully (from cache)",
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Wishlist of products from this user ID : {user_id} not found"
                ).dict()
            )

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
            'data': [wish.dict() for wish in wishlist_dto]
        }
        redis_client.setex(redis_key, CACHE_TTL, json.dumps(cache_data, default=custom_json_serializer))

        # Return DTO with success message
        return build(data=wishlist_dtos.AllWishlistResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message=f"All products wishlist for user ID {user_id} accessed successfully",
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
        return handle_db_error(db, e)
    
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

from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos

import json

from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_total, handle_db_error
# from app.services.cart_services.support_function import get_total_records

from app.utils.result import build, Result
from app.libs.redis_config import redis_client, custom_json_serializer

CACHE_TTL = 300

def my_cart(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 100
    ) -> Result[cart_dtos.AllCartResponseCreateDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"cart:{user_id}:{skip}:{limit}"

        # Check if wishlist data exists in Redis
        cached_cart = redis_client.get(redis_key)
        if cached_cart:
            # Data is found in cache, return it
            cart_data = json.loads(cached_cart)
            return build(data=cart_dtos.AllCartResponseCreateDto(
                status_code=status.HTTP_200_OK,
                message=f"All item products in cart from account user ID {user_id} accessed successfully (from cache)",
                total_prices=cart_data['total_prices'],
                data=cart_data['data']
            ))
        
        # Query untuk mengambil cart berdasarkan user_id dengan pagination
        cart_items = db.execute(
            select(CartProductModel)
            .where(CartProductModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"No products found in cart for user ID {user_id}."
                ).dict()
            )

        # Hitung total_records
        # total_records = get_total_records(db, user_id)

        # Konversi cart_items menjadi DTO
        cart_dto = [
            cart_dtos.CartInfoDetailDto(
                id=cart_item.id,
                product_name=cart_item.product_name,
                product_price=cart_item.product_price,
                variant_info=cart_item.variant_info,
                quantity=cart_item.quantity,
                is_active=cart_item.is_active,
                created_at=cart_item.created_at
            )
            for cart_item in cart_items
        ]

        cart_total_items_response = get_cart_total(cart_items)

        # Save the result to Redis cache
        cache_data = {
            'total_prices': cart_total_items_response,
            'data': [wish.dict() for wish in cart_dto]
        }
        redis_client.setex(redis_key, CACHE_TTL, json.dumps(cache_data, default=custom_json_serializer))

        # Return DTO dengan respons yang telah dibangun
        return build(data=cart_dtos.AllCartResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message=f"All products in cart for user ID {user_id} accessed successfully",
            # total_records=total_records,
            data=cart_dto,
            total_prices=cart_total_items_response
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
        return handle_db_error(db, e)
    
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
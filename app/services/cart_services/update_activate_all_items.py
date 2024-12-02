from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, load_only
from sqlalchemy.exc import SQLAlchemyError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_item, handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import redis_client

def update_activate_all_items(
        db: Session, 
        activate_update: cart_dtos.UpdateActivateItemDto,
        user_id: str
    ) -> Result[cart_dtos.CartInfoUpdateAllActivateResponseDto, Exception]:
    try:
        # Lakukan pembaruan langsung ke database
        updated_rows = db.query(CartProductModel)\
            .filter(CartProductModel.customer_id == user_id)\
            .update(
                {CartProductModel.is_active: activate_update.is_active},
                synchronize_session="fetch"
            )

        if updated_rows == 0:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cart items found for user ID {user_id}"
            ))

        # Commit perubahan
        db.commit()

        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"cart:{user_id}:*",
            f"carts:{user_id}"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        # Buat response
        return build(data=cart_dtos.CartInfoUpdateAllActivateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Successfully updated {updated_rows} cart items for user ID {user_id}.",
            # data=[]  # Data bisa disesuaikan jika hasil spesifik dibutuhkan
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ))

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        ))
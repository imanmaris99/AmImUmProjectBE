from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_item, handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import redis_client

# Fungsi untuk Mengupdate Status Aktif Item
def update_activate_item(
        db: Session, 
        cart: cart_dtos.UpdateByIdCartDto,
        activate_update: cart_dtos.UpdateActivateItemDto,
        user_id: str
        ) -> Result[Type[CartProductModel], Exception]:
    try:
        # Ambil item cart dari database
        activate_model = get_cart_item(db, cart.cart_id, user_id)

        if not activate_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Item product from this cart ID {cart.cart_id} Not Found"
                ).dict()
            ))

        # Update langsung atribut yang relevan
        if activate_update.is_active is not None:
            activate_model.is_active = activate_update.is_active

        # Simpan perubahan ke dalam database
        db.commit()

        # Refresh model untuk memastikan data terbaru
        db.refresh(activate_model)

        # Invalidasi cache dengan pendekatan yang lebih efisien
        redis_keys = [f"cart:{user_id}:*", f"carts:{user_id}"]
        for pattern in redis_keys:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        return build(data=cart_dtos.CartInfoUpdateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Updated Info Item from this Cart ID {cart.cart_id} has been success"
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
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

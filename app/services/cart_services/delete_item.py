from typing import Type

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.dtos import cart_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_item, handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import redis_client


# Fungsi untuk Mengupdate Kuantitas Item
def delete_item(
        db: Session, 
        cart: cart_dtos.UpdateByIdCartDto,
        user_id: str
        ) -> Result[None, Exception]:
    try:
        # Ambil item cart dari database
        cart_model = get_cart_item(db, cart.cart_id, user_id)

        if not cart_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Item product from this cart ID {cart.cart_id} Not Found"
                ).dict()
            ))

        data_info_item = cart_dtos.InfoDeleteCartDto(
                cart_id=cart_model.id,
                product_name=cart_model.product_name,
                variant_product=cart_model.variant_product
            )

        # Simpan perubahan ke dalam database   
        db.delete(cart_model)
        db.commit()

        # Invalidasi cache dengan pendekatan yang lebih efisien
        redis_keys = [f"cart:{user_id}:*", f"carts:{user_id}"]
        for pattern in redis_keys:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        return build(data=cart_dtos.DeleteCartResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Deleted Info Item from this Cart ID {cart.cart_id} has been success",
            data=data_info_item
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


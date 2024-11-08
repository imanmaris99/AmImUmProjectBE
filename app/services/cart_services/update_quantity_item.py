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



# Fungsi untuk Mengupdate Kuantitas Item
def update_quantity_item(
        db: Session, 
        cart: cart_dtos.UpdateByIdCartDto,
        quantity_update: cart_dtos.UpdateQuantityItemDto,
        user_id: str
        ) -> Result[Type[CartProductModel], Exception]:
    try:
        # Ambil item cart dari database
        quantity_model = get_cart_item(db, cart.cart_id, user_id)

        if not quantity_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Item product from this cart ID {cart.cart_id} Not Found"
                ).dict()
            ))

        # Update atribut berdasarkan input dari DTO
        for attr, value in quantity_update.model_dump().items():
            setattr(quantity_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(quantity_model)

        return build(data=cart_dtos.CartInfoUpdateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Updated Info Item from this Cart ID {cart.cart_id} has been success",
            data=cart_dtos.UpdateInfoCartItemDto(
                id=quantity_model.id,
                product_name=quantity_model.product_name,
                variant_product=quantity_model.variant_product,
                quantity=quantity_model.quantity,
                is_active=quantity_model.is_active
            )
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


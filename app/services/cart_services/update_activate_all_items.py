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


def update_activate_all_items(
        db: Session, 
        activate_update: cart_dtos.UpdateActivateItemDto,
        user_id: str
    ) -> Result[list[cart_dtos.UpdateInfoCartItemDto], Exception]:
    try:
        # Ambil semua item cart milik pengguna
        carts = db.execute(
            select(CartProductModel)
            .where(CartProductModel.customer_id == user_id)
        ).scalars().all()

        if not carts:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"No cart items found for user ID {user_id}"
                ).dict()
            ))

        # Update atribut `is_active` pada setiap item
        updated_items = []
        for cart in carts:
            for attr, value in activate_update.model_dump().items():
                setattr(cart, attr, value)
            updated_items.append(cart_dtos.UpdateInfoCartItemDto(
                id=cart.id,
                product_name=cart.product_name,
                variant_product=cart.variant_product,
                quantity=cart.quantity,
                is_active=cart.is_active
            ))

        # Commit perubahan ke database
        db.commit()

        return build(data=cart_dtos.CartInfoUpdateAllActivateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"All cart items for user ID {user_id} have been successfully updated",
            data=updated_items
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

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
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

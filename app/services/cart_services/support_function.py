from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result


def get_cart_total(cart_items) -> cart_dtos.CartProductTotalDto:
    active_items = [item for item in cart_items if item.is_active]
    all_promo_active_prices = sum(Decimal(item.total_promo or 0) for item in active_items)
    all_item_active_prices = sum(Decimal(item.total_price_no_discount or 0) for item in active_items)
    total_all_active_prices = all_item_active_prices - all_promo_active_prices
    
    return cart_dtos.CartProductTotalDto(
        all_promo_active_prices=all_promo_active_prices,
        all_item_active_prices=all_item_active_prices,
        total_all_active_prices=total_all_active_prices
    )

# Utility Function to Query Cart Item
def get_cart_item(db: Session, cart_id: str, user_id: str) -> CartProductModel:
    return db.execute(
        select(CartProductModel)
        .where(CartProductModel.id == cart_id, CartProductModel.customer_id == user_id)
    ).scalars().first()

#total product items in your cart have been successfully calculated
def get_total_records(db: Session, user_id: str):
    return db.execute(
        select(func.count())
        .select_from(CartProductModel)
        .where(CartProductModel.customer_id == user_id)
    ).scalar()

# Utility Function for Handling Database Errors
def handle_db_error(db: Session, error: SQLAlchemyError) -> Result:
    db.rollback()
    return build(error=HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ErrorResponseDto(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database error: {str(error)}"
        ).dict()
    ))

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.wishlist_model import WishlistModel
from app.dtos import wishlist_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result


#total product items in your cart have been successfully calculated
def get_total_records(db: Session, user_id: str):
    return db.execute(
        select(func.count())
        .select_from(WishlistModel)
        .where(WishlistModel.customer_id == user_id)
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

from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from app.models.cart_product_model import CartProductModel
from app.dtos import cart_dtos


def get_total_records(db: Session, user_id: str):
    return db.execute(
        select(func.count())
        .select_from(CartProductModel)
        .where(CartProductModel.customer_id == user_id)
    ).scalar()
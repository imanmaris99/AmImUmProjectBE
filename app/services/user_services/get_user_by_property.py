from typing import Type, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import BinaryExpression

from fastapi import HTTPException, status
from app.models.user_model import UserModel
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils import optional


def get_user_by_property(
    db: Session, 
    filter_property: Callable[[Type[UserModel]], BinaryExpression[bool]]
) -> optional.Optional[Type[UserModel], HTTPException]:
    try:
        # Query untuk mendapatkan user berdasarkan filter_property
        user_model: Type[UserModel] = db.query(UserModel).filter(filter_property(UserModel)).first()

        # Jika user ditemukan, kembalikan sebagai optional dengan data user
        if user_model:
            return optional.build(data=user_model)

        # Jika user tidak ditemukan, kembalikan error 404
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"User not found"
            ).dict()
        ))

    except SQLAlchemyError as e:
        # Menangani error database
        return optional.build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database error occurred while fetching user. {str(e)}"
            ).dict()
        ))


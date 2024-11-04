from typing import Type
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from fastapi import HTTPException, status

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils import optional

from .get_user_by_property import get_user_by_property


def get_user_by_email(db: Session, user_email: str) -> optional.Optional[Type[UserModel], HTTPException]:
    def user_filter(user_model: Type[UserModel]):
        return user_model.email.like(f"{user_email}")

    try:
        # Mendapatkan pengguna berdasarkan email dengan menggunakan filter
        user_opt = get_user_by_property(db=db, filter_property=user_filter)

        # Jika user ditemukan, kembalikan hasil sebagai optional dengan data
        if user_opt.data:
            return user_opt

        # Jika tidak ditemukan, kembalikan error Not Found
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"User with this email address {user_email} not found"
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

# def get_user_by_email(db: Session, user_email: str) -> optional.Optional[Type[UserModel], HTTPException]:
#     def user_filter(user_model: Type[UserModel]):
#         return user_model.email.like(f"{user_email}")

#     user_opt = get_user_by_property(db=db, filter_property=user_filter)

#     if user_opt.data:
#         return user_opt

#     return optional.build(error=HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND,
#         error="Not Found",
#         message="email is not register"
#     ))

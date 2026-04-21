from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs import password_lib
from app.libs.jwt_lib import jwt_service
from app.models.user_model import UserModel
from app.utils import optional

from .get_by_user_email import get_user_by_email


def user_login(db: Session, user: user_dtos.UserLoginPayloadDto) -> optional.Optional[UserModel, Exception]:
    if not user.email or not user.password:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Email and password must be provided."
            ).model_dump()
        ))

    try:
        user_optional = get_user_by_email(db, user.email)

        if user_optional.error or not user_optional.data:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="User with the provided email does not exist."
                ).model_dump()
            ))

        user_model = user_optional.data

        if not user_model.hash_password:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error="Unauthorized",
                    message="This account cannot use password login. Please use the sign-in method linked to your account."
                ).model_dump()
            ))

        if not user_model.is_active:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_403_FORBIDDEN,
                    error="Forbidden",
                    message="Your account is not active. Please contact support."
                ).model_dump()
            ))

        if not password_lib.verify_password(plain_password=user.password, hashed_password=user_model.hash_password):
            return optional.build(error=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error="Unauthorized",
                    message="Password does not match."
                ).model_dump()
            ))

        access_token = jwt_service.create_access_token({
            "id": user_model.id,
            "role": user_model.role
        })

        return optional.build(data={
            "access_token": access_token,
            "user": {
                "id": user_model.id,
                "email": user_model.email,
                "role": user_model.role,
                "is_active": user_model.is_active
            }
        })

    except SQLAlchemyError as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).model_dump()
        ))

    except HTTPException as e:
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="An unexpected error occurred during login."
            ).model_dump()
        ))

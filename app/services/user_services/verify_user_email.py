# app/services/verify_user_email.py

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.user_model import UserModel
from app.dtos.error_response_dtos import ErrorResponseDto
from app.dtos.user_dtos import EmailInfoVerificationRequestDto, EmailVerificationResponseDto
from app.utils import optional

def verify_user_email(code: str, email: str, db: Session) -> optional.Optional[EmailVerificationResponseDto, Exception]:
    # Validasi input kode verifikasi dan email
    if not code or not email:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message="Verification code and email must be provided."
            ).dict()
        ))

    try:
        # Cari pengguna berdasarkan email
        user = db.query(UserModel).filter(UserModel.email == email).first()

        if not user:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="User with the provided email does not exist."
                ).dict()
            ))

        if user.is_active:
            return optional.build(data=EmailVerificationResponseDto(
                status_code=status.HTTP_200_OK,
                message="Email already verified and account already active",
                data=EmailInfoVerificationRequestDto(
                    code=code,
                    email=email,
                    firstname=user.firstname,
                    lastname=user.lastname,
                    gender=user.gender,
                    role=user.role,
                    is_active=user.is_active
                )
            ))

        if user.verification_expiry and user.verification_expiry < datetime.utcnow():
            return optional.build(error=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Verification code has expired."
                ).dict()
            ))

        if user.verification_code != code:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Invalid verification code."
                ).dict()
            ))

        user.is_active = True
        user.verification_code = None
        user.verification_expiry = None
        db.commit()
        db.refresh(user)
        return optional.build(data=EmailVerificationResponseDto(
            status_code=status.HTTP_200_OK,
            message="Email successfully verified and account activated",
            data=EmailInfoVerificationRequestDto(
                code=code,
                email=email,
                firstname=user.firstname,
                lastname=user.lastname,
                gender=user.gender,
                role=user.role,
                is_active=user.is_active
            )
        ))

    except SQLAlchemyError as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An unexpected error occurred: {str(e)}"
            ).dict()
        ))

# app/services/verify_user_email.py

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.models.user_model import UserModel
from app.dtos.error_response_dtos import ErrorResponseDto
from app.dtos.user_dtos import EmailVerificationRequestDto, EmailInfoVerificationRequestDto, EmailVerificationResponseDto
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

        # Cek kode verifikasi
        if user.verification_code == code:
            user.is_active = True
            user.verification_code = None  # Hapus kode verifikasi setelah berhasil diverifikasi
            user.verification_expiry = None
            db.commit()
            return optional.build(data=EmailVerificationResponseDto(
                status_code=status.HTTP_200_OK,
                message="Email successfully verified and Your Account Already Actived",
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
        else:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Invalid verification code."
                ).dict()
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

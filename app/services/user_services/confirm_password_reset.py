
from fastapi import HTTPException, status
from firebase_admin import auth

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs import password_lib
from app.libs.jwt_lib import jwt_service
from app.utils import optional, error_parser

from app.models.user_model import UserModel

from app.utils.error_parser import is_valid_password
# from app.utils.logging_utils import log_password_reset_request

def confirm_password_reset(
        payload: user_dtos.ResetPasswordDto, 
        db: Session
    ):
    # Cek apakah password memenuhi kebijakan
    is_valid, error_message = is_valid_password(payload.new_password)
    if not is_valid:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message=error_message
            ).dict()
        ))    

    # Cari user berdasarkan email terlebih dahulu
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()

    # Validasi email
    if not user:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"User with this email address {payload.email} not found."
            ).dict()
        ))

    # Validasi kode verifikasi
    if user.verification_code != payload.code:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail=ErrorResponseDto(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                error="Verification Code not Allowed",
                message="Invalid verification code."
            ).dict()
        ))

    try:
        # Hash password baru dan simpan
        user.hash_password = password_lib.get_password_hash(payload.new_password)
        user.verification_code = None  # Hapus kode setelah reset password
        db.commit()

        return optional.build(data=user_dtos.ResetPasswordResponseDto(
            status_code=201,
            message="Your password has been reset successfully",
            data=payload
        ))
        
    except SQLAlchemyError:
        return optional.build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Failed to reset password: {str(e)}"
            ).dict()
        ))
    






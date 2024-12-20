from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.libs import password_lib

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.models.user_model import UserModel

from app.utils import optional
from app.utils.error_parser import is_valid_password


async def change_password(
    user_id: str, 
    payload: user_dtos.ChangePasswordDto, 
    db: Session
    ):
    try:
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

        # Langkah 1: Cari user berdasarkan ID
        user_model = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="User with the provided email does not exist in Database."
                ).dict()
            )

        # Langkah 2: Verifikasi password lama
        if not password_lib.verify_password(payload.old_password, user_model.hash_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    error="UnAuthorized",
                    message="Old password is incorrect"
                ).dict()
            )

        # Langkah 3: Update password baru
        user_model.hash_password = password_lib.get_password_hash(payload.new_password)
        db.commit()

        # return optional.build(data=None)
        return optional.build(data=user_dtos.ChangePasswordResponseDto(
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
                message=f"An unexpected error occurred: {str(e)}"
            ).dict()
        ))

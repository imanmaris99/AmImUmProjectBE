from typing import Type, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, UploadFile, status

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils import optional, find_errr_from_args
from app.libs.redis_config import redis_client

def user_edit(
        user_id: str,
        user: user_dtos.UserEditProfileDto, 
        db: Session 
    ):
    try:
        user_model: Type[UserModel] = db.query(UserModel).filter(UserModel.id == user_id).first()
        if user_model:
            for field, value in user.dict().items():
                setattr(user_model, field, value)

            db.commit()
            db.refresh(user_model)
            
            # Invalidate the cached wishlist for this user
            keys_to_invalidate = redis_client.scan_iter(f"user:{user_id}:*")
            for key in keys_to_invalidate:
                redis_client.delete(key)

            # return optional.build(data=user_model)
            return optional.build(data=user_dtos.UserEditResponseDto(
            status_code=status.HTTP_200_OK,
            message="Your profile has been successfully updated",
            data=user
        ))
        
        else:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                error="Not Found",
                message="User not found"
                )
            )
        
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
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))
    
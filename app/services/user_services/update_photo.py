import logging

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.redis_config import custom_json_serializer, redis_client
from app.libs.upload_image_to_supabase import upload_image_to_supabase, validate_file
from app.models.user_model import UserModel
from app.utils.result import build, Result

logger = logging.getLogger(__name__)


async def update_my_photo(
        db: Session, 
        user_id: str, 
        file: UploadFile
    ) -> Result[UserModel, Exception]:
    try:
        # Langkah 1: Mencari user yang ada
        user_model = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"User with ID {user_id} not found."
                ).dict()
            )

        # Langkah 2: Validasi file jika ada
        if file:
            validate_file(file)  # Panggil fungsi validasi

            logger.debug("Uploading profile photo for user_id=%s filename=%s", user_id, file.filename)

            # Upload gambar ke Supabase atau storage lain
            public_url = await upload_image_to_supabase(
                file,
                "AmimumProject-storage",
                user_id,
                folder_name="images/photo_profile",
                old_file_url=user_model.photo_url
            )

            if public_url is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        error="Internal Server Error",
                        message="Failed to upload image."
                    ).dict()
                )

            # Update photo_url pada user
            user_model.photo_url = public_url           

        # Simpan perubahan ke dalam database
        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        # Buat instance dari UserEditProfileDto
        user_response = user_dtos.UserEditPhotoProfileDto(
            photo_url=user_model.photo_url,
        )

        # Invalidate the cached wishlist for this user
        keys_to_invalidate = redis_client.scan_iter(f"user:{user_id}:*")
        for key in keys_to_invalidate:
            redis_client.delete(key)

        # return build(data=user_model)
        return build(data=user_dtos.UserEditPhotoProfileResponseDto(
            status_code=201,
            message="Your profile has been successfully updated",
            data=user_response
        ))

    except SQLAlchemyError as e:
        logger.exception("Database conflict while updating profile photo user_id=%s", user_id)
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return build(error=e)

    except Exception as e:
        logger.exception("Unexpected error while updating profile photo user_id=%s", user_id)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))
   



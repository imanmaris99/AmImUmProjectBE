from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, UploadFile, status

from app.models.user_model import UserModel
from app.dtos import user_dtos

from app.libs.upload_image_to_supabase import upload_image_to_supabase, validate_file
from app.utils.result import build, Result

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
                error="Not Found", 
                message="User not found"
            )

        # Langkah 2: Validasi file jika ada
        if file:
            validate_file(file)  # Panggil fungsi validasi

            # Debugging: Cek apakah file diterima
            print(f"File diterima untuk upload: {file.filename}")

            # Upload gambar ke Supabase atau storage lain
            public_url = await upload_image_to_supabase(
                file, 
                "AmimumProject-storage", 
                user_id, 
                folder_name="images/photo_profile", 
                old_file_url=user_model.photo_url
                )
            
            print(f"Public URL dari file yang diupload: {public_url}")
            
            if public_url is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    error="Internal Server Error",
                    message="Failed to upload image."
                )
            
            # Update photo_url pada user
            user_model.photo_url = public_url           

        # Simpan perubahan ke dalam database
        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        # return build(data=user_model)
        return build(data=user_dtos.UserEditPhotoProfileResponseDto(
            status_code=201,
            message="Your profile has been successfully updated",
            photo_url=user_model.photo_url
        ))

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        )



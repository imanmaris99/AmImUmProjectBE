from fastapi import HTTPException, UploadFile, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos

from app.libs.upload_image_to_supabase import upload_image_to_supabase, validate_file
from app.utils.result import build, Result

async def post_logo(
        db: Session,
        production_id: int, 
        user_id: str, 
        file: UploadFile
    ) -> Result[ProductionModel, Exception]:
    try:

        # Buat instance dari ProductionModel
        # logo_model = ProductionModel(fk_admin_id=user_id)
        # Ambil instance dari ProductionModel berdasarkan ID
        logo_model = db.query(ProductionModel).filter(ProductionModel.id == production_id).first()

        if not logo_model:
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
                folder_name="images/company_logo", 
                old_file_url=logo_model.photo_url
                )
            
            print(f"Public URL dari file yang diupload: {public_url}")
            
            if public_url is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    error="Internal Server Error",
                    message="Failed to upload image."
                )
            
            # Update photo_url pada user
            logo_model.photo_url = public_url           

        # Simpan perubahan ke dalam database
        db.add(logo_model)
        db.commit()
        db.refresh(logo_model)

        # Buat instance dari UserEditProfileDto
        user_response = production_dtos.PostLogoCompanyDto(
            photo_url=logo_model.photo_url,
        )

        # return build(data=user_model)
        return build(data=production_dtos.PostLogoCompanyResponseDto(
            status_code=200,
            message="Your profile has been successfully updated",
            data=user_response
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



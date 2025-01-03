from fastapi import HTTPException, UploadFile, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs.upload_image_to_supabase import upload_image_to_supabase, validate_file

from app.services.production_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import redis_client

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
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Production with ID {production_id} not found"
                ).dict()
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
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        error="Internal Server Error",
                        message=f"Failed to upload image: {str(e)}"
                    ).dict()
                )
            # Update photo_url pada user
            logo_model.photo_url = public_url           

        db.add(logo_model)
        db.commit()
        db.refresh(logo_model)

        # Buat instance dari UserEditProfileDto
        user_response = production_dtos.PostLogoCompanyDto(
            photo_url=logo_model.photo_url,
        )

        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"productions:*",
            f"all_brand_by_categories:*",
            f"brand_promotions:*",
            f"production:{production_id}"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        # return build(data=user_model)
        return build(data=production_dtos.PostLogoCompanyResponseDto(
            status_code=200,
            message="Your profile has been successfully updated",
            data=user_response
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        return build(error=http_ex)
    
    except Exception as e:
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))




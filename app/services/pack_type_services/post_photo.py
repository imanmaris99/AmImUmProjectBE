from fastapi import HTTPException, UploadFile, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import EditPhotoProductDto, EditPhotoProductResponseDto 
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs.upload_image_to_supabase import upload_image_to_supabase, validate_file

from app.services.pack_type_services.support_function import handle_db_error

from app.utils.result import build, Result

async def post_photo(
        db: Session,
        type_id: int, 
        user_id: str, 
        file: UploadFile
    ) -> Result[PackTypeModel, Exception]:
    try:

        # Buat instance dari ProductionModel
        # logo_model = ProductionModel(fk_admin_id=user_id)
        # Ambil instance dari ProductionModel berdasarkan ID
        image_model = db.query(PackTypeModel).filter(PackTypeModel.id == type_id).first()

        if not image_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about variant product with ID {type_id} not found"
                ).dict()
            ))

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
                folder_name="images/product_picture", 
                old_file_url=image_model.img
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
            image_model.img = public_url           

        # Simpan perubahan ke dalam database
        db.add(image_model)
        db.commit()
        db.refresh(image_model)

        # Buat instance dari UserEditProfileDto
        updated_response = EditPhotoProductDto(
            img=image_model.img,
        )

        # return build(data=user_model)
        return build(data=EditPhotoProductResponseDto(
            status_code=200,
            message="Edit photo product has been success",
            data=updated_response
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

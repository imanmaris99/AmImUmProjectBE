from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import TypeIdToUpdateDto, PackTypeEditInfoDto, VariantProductDto, PackTypeEditInfoResponseDto 
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

def update_stock(
        db: Session, 
        type_id_update: TypeIdToUpdateDto,
        type_update: PackTypeEditInfoDto
        ) -> Result[PackTypeModel, Exception]:
    try:
        # Mencari model PackType berdasarkan ID
        type_model = db.query(PackTypeModel).filter(PackTypeModel.id == type_id_update.type_id).first()
        if not type_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about variant product with ID {type_id_update.type_id} not found"
                ).dict()
            ))
        
        # Update atribut stock dan discount jika ada
        for attr, value in type_update.model_dump().items():
            setattr(type_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(type_model)

        # Buat response DTO
        response_data = PackTypeEditInfoDto(
            stock=type_model.stock,
            discount=type_model.discount
        )

        # return build(data=user_model)
        return build(data=PackTypeEditInfoResponseDto(
            status_code=200,
            message="Edit stock and discount product has been success",
            data=response_data
        ))
    
        # # Menggunakan model ter-update untuk membuat respons
        # return build(data=PackTypeEditInfoResponseDto(
        #     status_code=200,
        #     message="Your pack and variant type product has been updated",
        #     data=VariantProductDto(
        #         id=type_model.id,
        #         variant=type_model.variant,
        #         expiration=type_model.expiration,
        #         stock=type_model.stock,
        #         discount=type_model.discount,  # Ambil discount dari model
        #         created_at=type_model.created_at,
        #         updated_at=type_model.updated_at
        #     )
        # ))

    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args("pack_types", str(e.args))}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  
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


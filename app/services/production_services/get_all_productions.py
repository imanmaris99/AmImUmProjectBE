from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Type

from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error

from app.utils.result import build, Result



def get_all_productions(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[production_dtos.AllListProductionResponseDto, Exception]:
    try:
        # product_bies = db.query(ProductionModel).offset(skip).limit(limit).all()

        product_bies = db.execute(
            select(ProductionModel)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not product_bies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No information about productions found."
                ).dict()
            )

        # Konversi produk menjadi DTO
        productions_dto = [
            production_dtos.AllProductionsDto(
                id=production.id,  # Pastikan id adalah string
                name=production.name,
                photo_url=production.photo_url,
                description_list=production.description_list,  # Menggunakan property untuk mendapatkan deskripsi
                category=production.category,  # Menggunakan property untuk mendapatkan nama kategori
                created_at=production.created_at
            )
            for production in product_bies
        ]

        # return build(data=productions_dto)
    
        return build(data=production_dtos.AllListProductionResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List productS from this brand accessed successfully",
            data=productions_dto
        ))
    
    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
        return build(error=http_ex)
    
    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))

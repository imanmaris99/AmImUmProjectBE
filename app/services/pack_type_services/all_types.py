from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Type

from app.models.pack_type_model import PackTypeModel
from app.dtos.pack_type_dtos import VariantProductDto, PackTypeEditInfoResponseDto, VariantAllProductDto, AllVariantsProductInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.pack_type_services.support_function import handle_db_error

from app.utils import optional
from app.utils.result import build, Result


def all_types(
        db: Session, skip: int = 0, limit: int = 10
    ) -> Result[List[Type[PackTypeModel]], Exception]:
    try:
        pack_types = db.execute(
            select(PackTypeModel)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not pack_types:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"info about all variants of product not found"
                ).dict()
            )

        # Konversi produk menjadi DTO
        types_dto = [
            VariantAllProductDto(
                id=types.id, 
                product=types.product,
                name=types.name,
                img=types.img,
                variant=types.variant,
                expiration=types.expiration,
                stock=types.stock,
                discount=types.discount,
                discounted_price=types.discounted_price,
                updated_at=types.updated_at
            )
            for types in pack_types
        ]

        # return build(data=types_dto)
    
        return build(data=AllVariantsProductInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List variants from all products accessed successfully",
            data=types_dto
        ))
    
    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
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

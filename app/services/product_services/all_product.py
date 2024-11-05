from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Type

from app.models.product_model import ProductModel
from app.dtos.product_dtos import AllProductInfoDTO
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result


def all_product(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[List[Type[ProductModel]], Exception]:
    try:
        product_model = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type))  # Eager loading untuk pack_type
                .offset(skip)
                .limit(limit)
            ).scalars()  # Mengambil hasil sebagai scalar
            .all()
        )

        if not product_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"info about list of all products not found"
                ).dict()
            )
            # raise HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     error="Not Found",
            #     message="List products not found"
            # )

        # Konversi produk menjadi DTO, cek `all_variants` agar tidak menyebabkan error jika None
        all_products_dto = [
            AllProductInfoDTO(
                id=product.id, 
                name=product.name,
                price=product.price,
                all_variants=product.all_variants or [],  # Cek None dan default ke list kosong                
                created_at=product.created_at
            )
            for product in product_model
        ]

        return build(data=all_products_dto)

    except SQLAlchemyError as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
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

    # except SQLAlchemyError as e:
    #     print(e)
    #     db.rollback()
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         error="Conflict",
    #         message=f"Database conflict: {str(e)}"
    #     ))
    
    # except HTTPException as http_ex:
    #     return build(error=http_ex)
    
    # except Exception as e:
    #     print(e)
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         error="Internal Server Error",
    #         message=f"An error occurred: {str(e)}"
    #     ))
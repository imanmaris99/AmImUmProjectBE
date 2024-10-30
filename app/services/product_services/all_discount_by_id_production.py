from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Type

from app.models.product_model import ProductModel
from app.models.pack_type_model import PackTypeModel
from app.dtos.product_dtos import AllProductInfoDTO
from app.utils.result import build, Result

def all_discount_by_id_production(
        db: Session, 
        production_id: int,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[List[Type[ProductModel]], Exception]:
    try:
        # Subquery untuk mendapatkan produk yang memiliki pack type dengan diskon
        subquery = (
            select(PackTypeModel.product_id)
            .filter(PackTypeModel.discount > 0)
            .scalar_subquery()
        )

        # Mengambil produk yang aktif dan memiliki variasi dengan diskon
        product_model = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type))  # Eager loading untuk pack_type
                .where(ProductModel.product_by_id == production_id,
                       ProductModel.is_active.is_(True), 
                       ProductModel.id.in_(subquery))
                .offset(skip)
                .limit(limit)
            ).scalars()  # Mengambil hasil sebagai scalar
            .all()
        )

        # # Jika tidak ada produk ditemukan, kembalikan list kosong
        # if not product_model:
        #     return build(data=[])
        if not product_model:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"info about discount product of this brand Production with ID {production_id} not found"
            ))

        # Konversi produk menjadi DTO
        all_products_discount_by_production_dto = [
            AllProductInfoDTO(
                id=product.id, 
                name=product.name,
                price=product.price,
                all_variants=product.all_variants or [],  # Cek None dan default ke list kosong                
                created_at=product.created_at
            )
            for product in product_model
        ]

        return build(data=all_products_discount_by_production_dto)

    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Database conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))

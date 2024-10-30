from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload  # Menggunakan selectinload untuk efisiensi
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Type

from app.models.product_model import ProductModel
from app.models.pack_type_model import PackTypeModel  # Pastikan diimpor
from app.dtos.product_dtos import AllProductInfoDTO
from app.utils.result import build, Result

def all_product_with_discount(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[List[Type[ProductModel]], Exception]:
    try:
        # Subquery untuk mendapatkan produk yang memiliki pack type dengan diskon
        subquery = (
            select(PackTypeModel.product_id)
            .filter(PackTypeModel.discount > 0)
            .scalar_subquery()  # Menggunakan scalar_subquery()
        )

        # Mengambil produk yang aktif dan memiliki variasi dengan diskon
        product_model = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type))  # Eager loading untuk pack_type
                .where(ProductModel.is_active.is_(True), 
                        ProductModel.id.in_(subquery))  # Menggunakan in_() dengan subquery
                .offset(skip)
                .limit(limit)
            ).scalars().all()
        )

        if not product_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="list products have a discount not found"
            )

        # Konversi produk menjadi DTO
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
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {str(e)}"
        ))
    
    except HTTPException as http_ex:
        return build(error=http_ex)
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))

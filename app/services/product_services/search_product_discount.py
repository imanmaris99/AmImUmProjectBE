from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload  # Menggunakan selectinload untuk efisiensi
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Type

from app.models.product_model import ProductModel
from app.models.pack_type_model import PackTypeModel  # Pastikan diimpor
from app.dtos.product_dtos import AllProductInfoDTO
from app.utils.result import build, Result

def search_product_discount(
        db: Session, 
        product_name: str,
        skip: int = 0, 
        limit: int = 10
    ) -> Result[List[Type[ProductModel]], Exception]:
    try:
        # Subquery untuk produk dengan diskon
        subquery = (
            select(PackTypeModel.product_id)
            .filter(PackTypeModel.discount > 0)
            .scalar_subquery()
        )

        search_query = f"%{product_name}%"  # Pencarian menggunakan ilike
        
        # Query untuk produk yang cocok dengan nama dan aktif serta memiliki diskon
        product_model = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type))  # Eager loading untuk pack_type
                .filter(
                    ProductModel.name.ilike(search_query),
                    ProductModel.is_active.is_(True),
                    ProductModel.id.in_(subquery)
                )
                .offset(skip)
                .limit(limit)
            ).scalars().all()
        )

        if not product_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"No product have a discount found with name containing '{product_name}'."
            )

        # # Jika tidak ada produk ditemukan, kembalikan list kosong
        # if not product_model:
        #     return build(data=[])
        
        # Konversi produk menjadi DTO
        product_discount_dto = [
            AllProductInfoDTO(
                id=product.id, 
                name=product.name,
                price=product.price,
                all_variants=product.all_variants or [],  # Cek None dan default ke list kosong                
                created_at=product.created_at
            )
            for product in product_model
        ]

        return build(data=product_discount_dto)

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

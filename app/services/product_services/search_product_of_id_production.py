from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Type

from app.models.product_model import ProductModel
from app.dtos.product_dtos import AllProductInfoDTO
from app.utils.result import build, Result

def search_product_of_id_production(
        db: Session, 
        production_id: int,  
        product_name: str,
        skip: int = 0, 
        limit: int = 10
    ) -> Result[List[Type[ProductModel]], Exception]:  # Mengembalikan List DTO
    try:
        search_query = f"%{product_name}%"
        # Query untuk mengambil produk berdasarkan product_by_id
        product_model = db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.pack_type))  # Eager load untuk pack_type
            .where(
                ProductModel.product_by_id == production_id,
                ProductModel.name.ilike(search_query)
            )  
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not product_model:
            return build(data=[])  # Kembalikan list kosong jika tidak ada produk ditemukan

        # Konversi produk ke DTO
        all_products_dto = [
            AllProductInfoDTO(
                id=product.id, 
                name=product.name,
                price=product.price,
                all_variants=product.all_variants or [],                
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
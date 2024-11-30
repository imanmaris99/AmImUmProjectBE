from fastapi import HTTPException, status

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from typing import Dict, Any
import json

from app.models.product_model import ProductModel
from app.dtos import product_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client


def infinite_scrolling_list_products_by_id_production(
        db: Session, 
        production_id: int,
        skip: int = 0, 
        limit: int = 6
    ) -> Result[Dict[str, Any], Exception]:
    cache_key = f"products:{skip}:{limit}"

    try:
        # Cek data di Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON dari Redis dan kirim sebagai response
            cached_response = json.loads(cached_data)
            return build(data=cached_response)
        
        # Ambil data produk dengan lazy loading, ambil kolom yang relevan saja
        product_list = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type))  # Eager load untuk pack_type
                .where(ProductModel.product_by_id == production_id)  # Filter dengan production_id
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()

        if not product_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"info about list products from Production with ID {production_id} not found"
                ).dict()
            )

        # Hitung total_records
        total_records = db.execute(select(func.count()).select_from(ProductModel)).scalar()

        # Hitung sisa data
        displayed_records = skip + len(product_list)
        has_more = displayed_records < total_records

        # Konversi produk menjadi DTO
        products_dto = [
            product_dtos.AllProductInfoDTO(
                id=product.id, 
                name=product.name,
                price=product.price,
                all_variants=product.all_variants or [],                
                created_at=product.created_at
            )
            for product in product_list
        ]

        # Bangun respons dengan data produk dan has_more
        response_data = product_dtos.ProductListScrollResponseDto(
            data=products_dto,
            has_more=has_more
        )

        # Simpan data ke Redis (dengan TTL 300 detik)
        redis_client.setex(cache_key, 300, json.dumps(response_data.dict(), default=custom_json_serializer))

        return build(data=response_data)
    
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
    

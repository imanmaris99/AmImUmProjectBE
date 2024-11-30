from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

import json

from app.models.product_model import ProductModel
from app.dtos.product_dtos import AllProductInfoDTO, ProductInfoByIdProductionDTO, AllProductInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

def all_product_by_id_production(
        db: Session, 
        production_id: int,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[AllProductInfoResponseDto, Exception]:  
    cache_key = f"products:{skip}:{limit}"

    try:
        # Cek data di Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON dari Redis dan kirim sebagai response
            cached_response = json.loads(cached_data)
            return build(data=cached_response)
        
        product_model = db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.pack_type))  # Eager load untuk pack_type
            .where(ProductModel.product_by_id == production_id)  
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        # if not product_model:
        #     return build(data=[])  # Kembalikan list kosong jika tidak ada produk ditemukan
        if not product_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"info about list products from Production with ID {production_id} not found"
                ).dict()
            )

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

        # return build(data=all_products_dto)
    
        # return build(data=AllProductInfoResponseDto(
        #     status_code=status.HTTP_200_OK,
        #     message=f"All List of product by production with ID {production_id} can accessed successfully",
        #     data=all_products_dto
        # ))
        response_dto = AllProductInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List product can accessed successfully",
            data=all_products_dto
        )

        # Simpan data ke Redis (dengan TTL 300 detik)
        redis_client.setex(cache_key, 300, json.dumps(response_dto.dict(), default=custom_json_serializer))
        
        return build(data=response_dto)

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
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


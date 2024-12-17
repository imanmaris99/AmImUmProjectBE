from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

import json

from app.models.product_model import ProductModel

from app.models.pack_type_model import PackTypeModel
from app.dtos.product_dtos import AllProductInfoDTO, AllProductInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600

def all_discount_by_id_production(
        db: Session, 
        production_id: int,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[AllProductInfoResponseDto, Exception]:
    cache_key = f"discounts:{production_id}:{skip}:{limit}"

    try:
        # Cek data di Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON dari Redis dan kirim sebagai response
            cached_response = json.loads(cached_data)
            return build(data=cached_response)
        
        subquery = (
            select(PackTypeModel.product_id)
            .filter(PackTypeModel.discount > 0)
            .scalar_subquery()
        )

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
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"info about discount product from Production with ID {production_id} not found"
                ).dict()
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

        # return build(data=all_products_discount_by_production_dto)

        # return build(data=AllProductInfoResponseDto(
        #     status_code=status.HTTP_200_OK,
        #     message=f"All List of product discount with brand ID {production_id} can accessed successfully",
        #     data=all_products_discount_by_production_dto
        # ))
        response_dto = AllProductInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List product can accessed successfully",
            data=all_products_discount_by_production_dto
        )

        # Simpan data ke Redis (dengan TTL 300 detik)
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_dto.dict(), default=custom_json_serializer))
        
        return build(data=response_dto)
    
    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
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

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

import json

from app.models.product_model import ProductModel
from app.dtos.product_dtos import AllProductInfoDTO, AllProductInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600

def all_product(
        db: Session, 
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
            return build(data=AllProductInfoResponseDto(**cached_response))

        # Query ke database jika cache kosong
        product_model = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type)) 
                .offset(skip)
                .limit(limit)
            ).scalars()  
            .all()
        )

        if not product_model:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_204_NO_CONTENT,
                    error="No content found",
                    message="Info about list of all products not found"
                ).dict()
            )

        # Mapping data ke DTO
        all_products_dto = [
            AllProductInfoDTO(
                id=product.id, 
                name=product.name,
                price=product.price,
                brand_info=product.brand_info,
                all_variants=product.all_variants or [],  # Cek None dan default ke list kosong                
                created_at=product.created_at
            )
            for product in product_model
        ]

        response_dto = AllProductInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List product can accessed successfully",
            data=all_products_dto
        )

        redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_dto.dict(), default=custom_json_serializer))
        
        return build(data=response_dto)

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
    except Exception as e:
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))

import uuid

from sqlalchemy import select, cast, String
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from fastapi import HTTPException, status

import json

from app.models.product_model import ProductModel
from app.dtos.product_dtos import ProductDetailDTO, ProductDetailResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600  # 1 hour TTL for cache

def get_product_by_id(
        db: Session, 
        product_id: uuid.UUID
    ) -> Result[ProductDetailResponseDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"product:{product_id}"

        # Check if product data exists in Redis
        cached_product = redis_client.get(redis_key)
        if cached_product:
            product_detail_dto = ProductDetailDTO(**json.loads(cached_product))
            return build(data=ProductDetailResponseDto(
                status_code=200,
                message="Product details successfully retrieved (from cache)",
                data=product_detail_dto
            ))
        
        # Query to get product by ID with eager loading for related entities
        product_model = db.execute(
            select(ProductModel)
            .options(selectinload(ProductModel.pack_type))  # Eager load for pack_type
            .filter(cast(ProductModel.id, String) == str(product_id))
        ).scalars().first()

        # Check if product was found
        if not product_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about product with ID {product_id} not found"
                ).dict()
            ))

        # Convert the product to ProductDetailDTO
        product_detail_dto = ProductDetailDTO(
            id=product_model.id,
            name=product_model.name,
            info=product_model.info,
            variants_list=product_model.variants_list or [],
            description_list=product_model.description_list or [],
            instructions_list=product_model.instruction_list or [],
            price=product_model.price,
            is_active=product_model.is_active,
            company=product_model.company,
            avg_rating=product_model.avg_rating,
            total_rater=product_model.total_rater,
            created_at=product_model.created_at,
            updated_at=product_model.updated_at
        )

        # Cache the result in Redis
        redis_client.setex(redis_key, CACHE_TTL, json.dumps(product_detail_dto.dict(), default=custom_json_serializer))

        # Build success response
        return build(data=ProductDetailResponseDto(
            status_code=200,
            message="Product details successfully retrieved",
            data=product_detail_dto
        ))

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

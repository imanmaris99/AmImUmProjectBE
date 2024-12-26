from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload  # Menggunakan selectinload untuk efisiensi
from sqlalchemy.exc import SQLAlchemyError

from typing import List, Type
import json

from app.models.product_model import ProductModel
from app.models.pack_type_model import PackTypeModel  
from app.dtos.product_dtos import AllProductInfoDTO, AllProductInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600

def all_product_with_discount(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[AllProductInfoResponseDto, Exception]:
    cache_key = f"promotions:{skip}:{limit}"

    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            cached_response = AllProductInfoResponseDto.parse_obj(json.loads(cached_data))
            return build(data=cached_response)
        
        subquery = (
            select(PackTypeModel.product_id)
            .filter(PackTypeModel.discount > 0)
            .scalar_subquery()
        )

        product_model = (
            db.execute(
                select(ProductModel)
                .options(selectinload(ProductModel.pack_type))
                .where(ProductModel.is_active.is_(True), 
                        ProductModel.id.in_(subquery))
                .offset(skip)
                .limit(limit)
            ).scalars().all()
        )

        if not product_model:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="No products with discounts found."
            )

        all_products_dto = [
            AllProductInfoDTO(
                id=str(product.id),
                name=product.name or "No Name",
                price=product.price or 0.0,
                brand_info=product.brand_info or "Unknown Brand",
                all_variants=product.all_variants or [],
                created_at=product.created_at or "1970-01-01T00:00:00Z"
            )
            for product in product_model
        ]

        response_dto = AllProductInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All products with discount retrieved successfully.",
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
            detail=f"An error occurred: {str(e)}"
        ))

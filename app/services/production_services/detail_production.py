import uuid
from sqlalchemy import select, cast, String, func
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from fastapi import HTTPException, status

import json
import logging

from app.models.production_model import ProductionModel
from app.models.product_model import ProductModel
from app.models.pack_type_model import PackTypeModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 300
RESPONSE_MESSAGE = "Production detail retrieved successfully"

def detail_production(
        db: Session, 
        production_id: int,
    ) -> Result[ProductionModel, Exception]:
    try:
        # Redis key for caching
        redis_key = f"production:{production_id}"

        # Check if product data exists in Redis
        cached_product = None
        if redis_client:
            try:
                cached_product = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read production detail cache for key %s: %s", redis_key, cache_error)
        if cached_product:
            production_detail_dto = production_dtos.DetailProductionDto(**json.loads(cached_product))
            return build(data=production_dtos.ProductionDetailResponseDto(
                status_code=200,
                message=RESPONSE_MESSAGE,
                data=production_detail_dto
            ))
        
        production_model = db.execute(
            select(ProductionModel)
            .filter(ProductionModel.id == production_id)
        ).scalars().first()

        # Check if product was found
        if not production_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Production with ID {production_id} not found"
                ).dict()
            ))

        # Compute product counters from live relational data to avoid stale totals
        live_total_product = db.execute(
            select(func.count(ProductModel.id)).where(ProductModel.product_by_id == production_id)
        ).scalar() or 0

        live_total_product_with_promo = db.execute(
            select(func.count(func.distinct(ProductModel.id)))
            .select_from(ProductModel)
            .join(PackTypeModel, PackTypeModel.product_id == ProductModel.id)
            .where(
                ProductModel.product_by_id == production_id,
                func.coalesce(PackTypeModel.discount, 0) > 0
            )
        ).scalar() or 0

        # Convert the product to ProductDetailDTO
        production_detail_dto = production_dtos.DetailProductionDto(
            id=production_model.id,
            name=production_model.name,
            photo_url=production_model.photo_url,
            description_list=production_model.description_list or [],
            category=production_model.category,
            total_product=int(live_total_product),
            total_product_with_promo=int(live_total_product_with_promo),
            created_at=production_model.created_at
        )

        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(production_detail_dto.dict(), default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write production detail cache for key %s: %s", redis_key, cache_error)

        # Build success response
        return build(data=production_dtos.ProductionDetailResponseDto(
            status_code=200,
            message=RESPONSE_MESSAGE,
            data=production_detail_dto
        ))

    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))
    
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


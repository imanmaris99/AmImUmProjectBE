from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
import json

from app.models.product_model import ProductModel
from app.models.production_model import ProductionModel
from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.production_services.support_function import handle_db_error
from app.utils.result import build, Result
from app.libs.redis_config import redis_client

CACHE_TTL = 300

def get_all_promo(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[production_dtos.AllProductionPromoResponseDto, Exception]:
    cache_key = f"brand_promotions:{skip}:{limit}"

    try:
        # Check Redis cache
        cached_data = redis_client.get(cache_key)
        if cached_data:
            # Parse JSON from Redis
            cached_response = json.loads(cached_data)
            return build(data=production_dtos.AllProductionPromoResponseDto(
                status_code=status.HTTP_200_OK,
                message="All promotions retrieved successfully (from cache)",
                data=cached_response['data']
            ))

        # Query database for promotions
        product_bies = (
            db.query(ProductionModel)
            .options(joinedload(ProductionModel.products))  # Eager loading of related products
            .join(ProductModel)
            .filter(
                ProductModel.is_active.is_(True),
                ProductionModel.products != None  # Only those with associated products
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        if not product_bies:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No information about promotions found."
                ).dict()
            )

        # Convert data to promo DTO
        info_promo = [
            production_dtos.AllProductionPromoDto(
                id=prod.id,  # UUID to string
                name=prod.name,
                photo_url=prod.photo_url,
                promo_special=prod.promo_special
            )
            for prod in product_bies if prod.promo_special > 0  # Only those with promo
        ]

        # Save the result to Redis cache
        cache_data = {
            'data': [brand.dict() for brand in info_promo]
        }
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_data))

        # Return response
        return build(data=production_dtos.AllProductionPromoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All promotions retrieved successfully.",
            data=info_promo
        ))

    except SQLAlchemyError as e:
        # Handle database errors
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()  # Only rollback if necessary
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

import json
import logging
import os

from app.models.product_model import ProductModel
from app.models.product_image_model import ProductImageModel
from app.dtos.product_dtos import AllProductInfoDTO, AllProductInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.product_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

logger = logging.getLogger(__name__)

CACHE_TTL = 3600
RESPONSE_MESSAGE = "All List product can accessed successfully"


def _normalize_image_url(url: str | None) -> str | None:
    if not url:
        return url
    if "127.0.0.1" not in url and "localhost" not in url:
        return url
    host_url = os.getenv("HOST_URL", "").rstrip("/")
    if not host_url:
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
        if railway_domain:
            host_url = f"https://{railway_domain.strip('/')}"
    if not host_url:
        return url
    try:
        path = url.split("/images/", 1)[1]
        return f"{host_url}/images/{path}"
    except Exception:
        return url

def all_product(
        db: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> Result[AllProductInfoResponseDto, Exception]:
    cache_key = f"products:{skip}:{limit}"
    
    try:
        # Cek data di Redis cache
        cached_data = None
        if redis_client:
            try:
                cached_data = redis_client.get(cache_key)
            except Exception as cache_error:
                logger.warning("Failed to read product cache for key %s: %s", cache_key, cache_error)

        if cached_data:
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
            return build(data=AllProductInfoResponseDto(
                status_code=status.HTTP_200_OK,
                message=RESPONSE_MESSAGE,
                data=[]
            ))

        # Mapping data ke DTO
        all_products_dto = []
        for product in product_model:
            product_images = []
            gallery_images = []
            default_image_url = os.getenv("DEFAULT_PRODUCT_IMAGE_URL")
            primary_image = default_image_url

            try:
                product_images = db.query(ProductImageModel).filter(
                    ProductImageModel.product_id == str(product.id)
                ).order_by(ProductImageModel.sort_order.asc(), ProductImageModel.id.asc()).all()

                gallery_images = [
                    {
                        "id": img.id,
                        "url": _normalize_image_url(img.url),
                        "is_primary": img.is_primary,
                        "sort_order": img.sort_order,
                    } for img in product_images
                ]
                primary_image = _normalize_image_url(next((img.url for img in product_images if img.is_primary), None)) or default_image_url
            except Exception as image_error:
                logger.warning("Failed to load product images for product %s: %s", product.id, image_error)

            all_products_dto.append(AllProductInfoDTO(
                id=product.id,
                name=product.name,
                price=float(product.price),
                min_variant_price=product.min_variant_price,
                max_variant_price=product.max_variant_price,
                brand_info=product.brand_info,
                primary_image_url=primary_image,
                gallery_images=gallery_images,
                all_variants=product.all_variants or [],
                created_at=product.created_at
            ))

        response_dto = AllProductInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            data=all_products_dto
        )

        if redis_client:
            try:
                redis_client.setex(cache_key, CACHE_TTL, json.dumps(response_dto.model_dump(), default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write product cache for key %s: %s", cache_key, cache_error)
        
        return build(data=response_dto)

    except SQLAlchemyError as e:
        return build(error=handle_db_error(db, e))
    
    except HTTPException as http_ex:
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

from sqlalchemy.orm import Session
from sqlalchemy import select

from fastapi import HTTPException, status

import json

from app.models.tag_category_model import TagCategoryModel
from app.dtos.category_dtos import AllCategoryResponseDto, AllCategoryInfoResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600  # Cache TTL dalam detik (1 jam)

def get_all_categories(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[AllCategoryInfoResponseDto, Exception]:
    cache_key = f"categories:{skip}:{limit}"

    try:
        # Check if product data exists in Redis
        cached_categorie = redis_client.get(cache_key)

        if cached_categorie:
            categories_data = [
                AllCategoryResponseDto(**addr)
                for addr in json.loads(cached_categorie)
            ]
            return build(data=AllCategoryInfoResponseDto(
                status_code=status.HTTP_200_OK,
                message="All lists of categories successfully retrieved (from cache)",
                data=categories_data
            ))
                
        categories = db.execute(
            select(TagCategoryModel)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not categories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="Categories not found"
                ).dict()
            )

        # Konversi kategori ke DTO
        categories_data = [
            AllCategoryResponseDto(
                id=category.id,
                name=category.name,
                description_list=category.description_list,
                created_at=category.created_at
            ) for category in categories
        ]

        # Cache the data in Redis
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(
            [dto.dict() for dto in categories_data], 
            default=custom_json_serializer
        ))

        # return build(data=response_data)
        return build(data=AllCategoryInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List of tag Categories accessed successfully",
            data=categories_data
        ))

    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return build(error=e)
    
    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))


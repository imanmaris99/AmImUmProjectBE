from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.models.tag_category_model import TagCategoryModel
from app.dtos.category_dtos import AllCategoryResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result


def get_all_categories(
        db: Session, skip: int = 0, limit: int = 10
    ) -> Result[List[AllCategoryResponseDto], Exception]:
    try:
        categories = db.query(TagCategoryModel).offset(skip).limit(limit).all()

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
        response_data = [
            AllCategoryResponseDto(
                id=category.id,
                name=category.name,
                description_list=category.description.split("\n"),
                created_at=category.created_at
            ) for category in categories
        ]

        return build(data=response_data)

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


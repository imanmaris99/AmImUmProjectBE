from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.dtos import category_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.models.tag_category_model import TagCategoryModel

from app.services.article_services.update_article import delete_cache_by_pattern
from app.utils import optional
from app.utils.result import build, Result

def create_categories(
        db: Session, 
        tag_category: category_dtos.CategoryCreateDto
        ) -> Result[TagCategoryModel, Exception]:
    try:
        category_model = TagCategoryModel(**tag_category.model_dump())
        db.add(category_model)
        db.commit()
        db.refresh(category_model)

        # Buat DTO response
        categories_response = category_dtos.AllCategoryResponseDto(
            id=category_model.id,
            name=category_model.name,
            description_list=category_model.description_list,
            created_at=category_model.created_at
        )

        # Invalidate Redis cache
        delete_cache_by_pattern("categories:*")
        
        return optional.build(data=category_dtos.CategoryCreateResponseDto(
            status_code=201,
            message="Create tag categories has been successfully updated",
            data=categories_response
        ))
    
    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database Error: Failed to create categories. {str(e)}"
            ).dict()
        ))
    
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
    

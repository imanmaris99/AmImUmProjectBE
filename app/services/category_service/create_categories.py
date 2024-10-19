from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.dtos import category_dtos
from app.models.tag_category_model import TagCategoryModel

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

        return optional.build(data=category_dtos.CategoryCreateResponseDto(
            status_code=201,
            message="Create tag categories has been successfully updated",
            data=tag_category
        ))
    
    except SQLAlchemyError as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message="failed to create business category"
        ))
    
    except Exception as e:
        db.rollback()  # Rollback untuk error tak terduga
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Unexpected error: {str(e)}"
        ))
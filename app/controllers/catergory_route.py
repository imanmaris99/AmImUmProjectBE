from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from app.dtos import category_dtos
from app.models.tag_category_model import TagCategoryModel

from app.services import category_service
from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/categories",
    tags=["Tag-Categories"]
)

@router.post(
        "/", 
        response_model=category_dtos.CategoryCreateResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def create_article(
    category_create_dto: category_dtos.CategoryCreateDto, 
    db: Session = Depends(get_db),
):
    result = category_service.create_categories(
        db, 
        category_create_dto
    )
    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
        "/", 
        response_model=List[category_dtos.AllCategoryResponseDto]
    )
def read_categories(
    # jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],    
    db: Session = Depends(get_db)
):
    result = category_service.get_all_categories(db)
    return result.unwrap()
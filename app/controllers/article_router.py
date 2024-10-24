# routes/article_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from app.dtos.article_dtos import ArticleCreateDTO, ArticleIdToUpdateDto, ArticleDataUpdateDTO, ArticleInfoUpdateResponseDto, ArticleResponseDTO, GetAllArticleDTO, DeleteArticleDto, DeleteArticleResponseDto
from app.services import article_services
from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/articles",
    tags=["Articles"]
)

@router.post(
        "/", 
        response_model=ArticleResponseDTO,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def create_article(
    article_create_dto: ArticleCreateDTO, 
    db: Session = Depends(get_db),
):
    result = article_services.create_article(db, article_create_dto)
    if result.error:
        raise result.error
    return result.data

@router.get(
        "/", 
        response_model=List[GetAllArticleDTO]
    )
def read_articles(
    # jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],    
    db: Session = Depends(get_db)
):
    result = article_services.get_articles(db)
    return result.unwrap()

@router.put(
        "/{article_id}", 
        response_model=ArticleInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def update_article(
    article_id_update: ArticleIdToUpdateDto, 
    article_update_dto: ArticleDataUpdateDTO,
    db: Session = Depends(get_db)
):
    result = article_services.update_article(db, article_id_update, article_update_dto)
    
    if result.error:
        raise result.error
    
    return result.data

@router.delete(
        "/delete/{article_id}", 
        response_model= DeleteArticleResponseDto,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def delete_article(
    article_data: DeleteArticleDto, 
    db: Session = Depends(get_db)
):
    result = article_services.delete_article(
        db, 
        article_data=article_data
    )

    if result.error:
        raise result.error
    
    return result.unwrap()
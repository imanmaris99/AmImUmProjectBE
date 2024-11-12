# services/article_service.py

from fastapi import HTTPException, status

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.article_model import ArticleModel
from app.dtos import article_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from typing import List, Type

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

    
def get_articles(
        db: Session, 
        skip: int = 0, 
        limit: int = 10
    ) -> Result[article_dtos.AllArticleResponseDto, Exception]:
    try:
        # article=db.query(ArticleModel)\
        #     .order_by(ArticleModel.display_id)\
        #     .offset(skip).limit(limit).all()

        article = db.execute(
            select(ArticleModel)
            .order_by(ArticleModel.display_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not article:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Articles not found"
                ).dict()
            ))

        # Konversi wishlist menjadi DTO
        article_dto = [
            article_dtos.GetAllArticleDTO(
                display_id=art.display_id,
                title=art.title,
                img=art.img,
                description_list=art.description_list
            )
            for art in article
        ]

        return build(data=article_dtos.AllArticleResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"All List of Article accessed successfully",
            data=article_dto
        ))


    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args("articles", str(e.args))}"
            ).dict()
        ))
    
    except Exception as e:
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))

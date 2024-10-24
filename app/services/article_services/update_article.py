# services/article_service.py

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.article_model import ArticleModel
from app.dtos.article_dtos import ArticleIdToUpdateDto, ArticleDataUpdateDTO, ArticleInfoUpdateResponseDto

from app.utils import optional
from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

    
def update_article(
        db: Session, 
        article_id_update: ArticleIdToUpdateDto,
        article_update: ArticleDataUpdateDTO
        ) -> Result[ArticleModel, Exception]:
    try:
        article = db.query(ArticleModel).filter(ArticleModel.id == article_id_update.article_id).first()
        if not article:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="Article not found"
            ))
        
        # Update atribut bisnis
        for attr, value in article_update.model_dump().items():
            setattr(article, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(article)
        return build(data=ArticleInfoUpdateResponseDto(
            status_code=200,
            message="Information about some article has been updated",
            data=ArticleDataUpdateDTO(
                title=article.title,
                description=article.description
            )
        ))
    
    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            error="Conflict",
            message=f"Database conflict: {find_errr_from_args("articles", str(e.args))}"
        ))
    
    except Exception as e:
        print(e)
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred: {str(e)}"
        ))

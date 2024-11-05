# services/article_service.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.article_model import ArticleModel
from app.dtos.article_dtos import ArticleIdToUpdateDto, ArticleDataUpdateDTO, ArticleInfoUpdateResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

def update_article(
        db: Session, 
        article_id_update: ArticleIdToUpdateDto,
        article_update: ArticleDataUpdateDTO
        ) -> Result[ArticleInfoUpdateResponseDto, Exception]:
    try:
        # Mencari artikel berdasarkan ID
        article = db.query(ArticleModel).filter(ArticleModel.id == article_id_update.article_id).first()
        if not article:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Articles with ID {article_id_update.article_id} not found"
                ).dict()
            ))
            # return build(error=HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     error="Not Found",
            #     message="Artikel tidak ditemukan"
            # ))
        
        # Update atribut artikel
        for attr, value in article_update.model_dump().items():
            setattr(article, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(article)

        return build(data=ArticleInfoUpdateResponseDto(
            status_code=status.HTTP_200_OK,
            message="Updated Info about some article has been success",
            data=ArticleDataUpdateDTO(
                title=article.title,
                description=article.description
            )
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
    # except SQLAlchemyError as e:
    #     db.rollback()  # Rollback untuk error SQLAlchemy
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         error="Conflict",
    #         message=f"Database conflict: {find_errr_from_args('articles', str(e.args))}"
    #     ))
    
    # except Exception as e:
    #     db.rollback()  # Rollback untuk error tak terduga
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         error="Internal Server Error",
    #         message=f"An error occurred: {str(e)}"
    #     ))

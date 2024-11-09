# services/article_service.py

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.article_model import ArticleModel
from app.dtos.article_dtos import ArticleCreateDTO, ArticleResponseDTO, ArticleCreateResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils import optional
from app.utils.result import build, Result

    
def create_article(
        db: Session, articles: ArticleCreateDTO
        ) -> Result[ArticleModel, Exception]:
    try:
        # Mengatur display_id secara otomatis
        display_id = ArticleModel.set_display_id(db)
        
        # Buat model artikel baru dengan data dari DTO
        article = ArticleModel(**articles.model_dump(), display_id=display_id)  # Gunakan display_id yang dihitung
        db.add(article)
        db.commit()
        db.refresh(article)

        article_new_dto = ArticleResponseDTO(
            id=article.id,
            display_id=article.display_id,
            title=article.title,
            img=article.img,
            description_list=article.description_list,
            created_at=article.created_at
        )

        return build(data=ArticleCreateResponseDto(
            status_code=status.HTTP_201_CREATED,
            message="Successfully created new article",
            data=article_new_dto
        ))
        
    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Database Error: Failed to create article. {str(e)}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"            
            ).dict()
        ))

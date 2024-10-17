# services/article_service.py

from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.article_model import ArticleModel
from app.dtos.article_dtos import ArticleCreateDTO
from typing import List, Optional

from app.utils import optional
from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

    
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
        return build(data=article)
    
    except SQLAlchemyError as e:
        db.rollback()  # Rollback untuk semua error SQLAlchemy umum lainnya
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message="An error occurred while creating the user. Please try again later."
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        # Langsung kembalikan error dari Firebase tanpa membuat response baru
        return build(error=http_ex)

    except Exception as e:
        db.rollback()  # Rollback untuk error tak terduga
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Unexpected error: {str(e)}"
        ))

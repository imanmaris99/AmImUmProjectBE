from fastapi import HTTPException, status

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.article_model import ArticleModel
from app.dtos.article_dtos import DeleteArticleDto, InfoDeleteArticleDto, DeleteArticleResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.result import build, Result
from app.utils.error_parser import find_errr_from_args

def reorder_ids(session: Session):
    """Mengatur ulang display_id untuk semua artikel berdasarkan urutan created_at."""
    articles = session.query(ArticleModel).order_by(ArticleModel.created_at).all()
    
    # Set display_id secara berurutan
    for index, article in enumerate(articles, start=1):
        article.display_id = index
    
    session.commit()

def delete_article(
        db: Session, 
        article_data: DeleteArticleDto,
        ) -> Result[None, Exception]:
    """Menghapus artikel berdasarkan ID dan mengatur ulang display_id."""
    try:
        article = db.query(ArticleModel).filter(ArticleModel.id == article_data.article_id).first()
        if not article:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Article with ID {article_data.article_id} not found"
                ).dict()
            ))
            # return build(error=HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     error="Not Found",
            #     message=f"Article with ID {article_data.article_id} not found"
            # ))
        
        # Simpan informasi pengguna sebelum dihapus
        article_delete_info = InfoDeleteArticleDto(
            article_id= article.id,
            title= article.title
        )

        # Hapus artikel
        db.delete(article)
        db.commit()

        # Panggil reorder_ids setelah penghapusan
        reorder_ids(db)

        return build(data=DeleteArticleResponseDto(
            status_code=200,
            message="Your article has been deleted",
            data=article_delete_info
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
    #     print(e)
    #     db.rollback()
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         error="Conflict",
    #         message=f"Database conflict: {find_errr_from_args("articles", str(e.args))}"
    #     ))
    
    # except Exception as e:
    #     print(e)
    #     return build(error=HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         error="Internal Server Error",
    #         message=f"An error occurred: {str(e)}"
    #     ))

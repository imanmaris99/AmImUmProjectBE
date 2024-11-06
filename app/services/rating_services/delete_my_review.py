# services/article_service.py

from typing import Type

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.rating_model import RatingModel
from app.dtos import rating_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result

def delete_my_review(
        db: Session, 
        review_id_delete: rating_dtos.DeleteReviewDto,
        user_id: str
        ) -> Result[None, Exception]:
    try:
        rate_model = db.execute(
            select(RatingModel)
            .where(
                RatingModel.id == review_id_delete.rating_id,
                RatingModel.user_id == user_id
            )  
        ).scalars().first()
        
        if not rate_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Review and rating from this product ID {review_id_delete.rating_id} Not Found"
                ).dict()
            ))
        
        review_delete_info = rating_dtos.InfoDeleteReviewDto(
            rating_id= rate_model.id,
            rate=rate_model.rate,
            review=rate_model.review,
            product_name=rate_model.product_name
        )

        # Simpan perubahan ke dalam database   
        db.delete(rate_model)
        db.commit()

        return build(data=rating_dtos.DeleteReviewResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Review and rating from this product ID {review_id_delete.rating_id} has been success to deleted",
            data=review_delete_info
        ))
    
    except SQLAlchemyError:
        db.rollback()
        return build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {find_errr_from_args("productions", str(e.args))}"
            ).dict()
        ))
    
    except HTTPException as http_ex:
        db.rollback()  
        return build(error=http_ex)
    
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

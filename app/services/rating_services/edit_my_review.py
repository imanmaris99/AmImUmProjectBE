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

def edit_my_review(
        db: Session, 
        review_id_update: rating_dtos.ReviewIdToUpdateDto,
        review_update: rating_dtos.ReviewDataUpdateDTO,
        user_id: str
        ) -> Result[Type[RatingModel], Exception]:
    try:
        rate_model = db.execute(
            select(RatingModel)
            .where(
                RatingModel.id == review_id_update.rating_id,
                RatingModel.user_id == user_id
            )  
        ).scalars().first()
        
        if not rate_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Review and rating from this product ID {review_id_update.rating_id} Not Found"
                ).dict()
            ))
        
        for attr, value in review_update.model_dump().items():
            setattr(rate_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(rate_model)

        return build(data=rating_dtos.ReviewInfoUpdateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Updated Info about Review and rating from this product ID {review_id_update.rating_id} has been success",
            data=rating_dtos.ReviewDataUpdateDTO(
                rate=rate_model.rate,
                review=rate_model.review
            )
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
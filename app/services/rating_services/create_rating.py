import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.product_model import ProductModel
from app.models.rating_model import RatingModel
from app.dtos.rating_dtos import RatingCreateOfIdProductDto, RatingCreateDto, RatingInfoCreateDto, RatingResponseCreateDto

from app.utils.result import build, Result

def create_rating(
        db: Session, 
        product_id: uuid.UUID,
        create_rate: RatingCreateDto,
        user_id: str
) -> Result[RatingModel, Exception]:
    try:
        # Cek apakah product_id ada di tabel products
        product = db.query(ProductModel).filter(ProductModel.id == str(product_id)).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message=f"Product with id {product_id} not found"
            )

        rate_instance = RatingModel(
            **create_rate.model_dump()
        )
        rate_instance.product_id = str(product_id)  # Konversi UUID ke string
        rate_instance.user_id = user_id
        db.add(rate_instance)
        db.commit()
        db.refresh(rate_instance)

        create_rate_response = RatingInfoCreateDto(
            id=rate_instance.id,
            rate=rate_instance.rate,
            review=rate_instance.review,
            product_name=rate_instance.product_name,
            rater_name=rate_instance.rater_name,
            created_at=rate_instance.created_at
        )

        return build(data=RatingResponseCreateDto(
            status_code=201,
            message="Your rating for the product has been created",
            data=create_rate_response
        ))


    except SQLAlchemyError as e:
        db.rollback()  # Rollback untuk semua error SQLAlchemy umum lainnya
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An error occurred : {str(e)}"
        ))
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        return build(error=http_ex)

    except Exception as e:
        db.rollback()  # Rollback untuk error tak terduga
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Unexpected error: {str(e)}"
        ))

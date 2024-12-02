from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

import json

from app.models.rating_model import RatingModel
from app.dtos.rating_dtos import MyRatingListDto, AllMyRatingListResponseDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.rating_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600 

def my_rating_list(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[AllMyRatingListResponseDto, Exception]:  # Mengembalikan List DTO
    try:
        # Redis key for caching
        redis_key = f"ratinglists:{user_id}:{skip}:{limit}"

        # Check if address data exists in Redis
        cached_rates = redis_client.get(redis_key)
        if cached_rates:
            all_rate_products_dto = [
                MyRatingListDto(**addr)
                for addr in json.loads(cached_rates)
            ]

            return build(data=AllMyRatingListResponseDto(
                status_code=status.HTTP_200_OK,
                message="All lists of rating product successfully retrieved (from cache)",
                data=all_rate_products_dto
            ))

        # Query untuk mengambil produk berdasarkan product_by_id
        rate_model = db.execute(
            select(RatingModel)
            .where(RatingModel.user_id == user_id)  # Filter dengan production_id
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not rate_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"list rate of products from this user ID : {user_id} not found"
                ).dict()
            )

        # Konversi produk ke DTO
        all_rate_products_dto = [
            MyRatingListDto(
                id=rate_count.id, 
                rate=rate_count.rate,
                review=rate_count.review,
                product_name=rate_count.product_name,                
                created_at=rate_count.created_at
            )
            for rate_count in rate_model
        ]

        # Cache the data in Redis
        redis_client.setex(redis_key, CACHE_TTL, json.dumps(
            [dto.dict() for dto in all_rate_products_dto], 
            default=custom_json_serializer
        ))

        # return build(data=all_rate_products_dto)
        return build(data=AllMyRatingListResponseDto(
            status_code=status.HTTP_200_OK,
            message="All List of your rating products accessed successfully",
            data=all_rate_products_dto
        ))

    # Error SQLAlchemy untuk data yang tidak valid, seperti id tidak ditemukan
    except IntegrityError as ie:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database integrity error: {str(ie)}"
            ).dict()
        ))

    # Error SQLAlchemy untuk data input yang tidak sesuai tipe
    except DataError as de:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error="Unprocessable Entity",
                message=f"Data error: {str(de)}"
            ).dict()
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        return build(error=http_ex)
    
        # Error tipe data tidak valid (misal, `skip` atau `limit` bukan integer)
    except (ValueError, TypeError) as te:
        return build(error=HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponseDto(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error="Unprocessable Entity",
                message=f"Invalid input: {str(te)}"
            ).dict()
        ))
    
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

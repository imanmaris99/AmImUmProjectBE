from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from typing import List, Type

from app.models.courier_model import CourierModel
from app.dtos import courier_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.utils.result import build, Result

def my_courier(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[courier_dtos.AllCourierListResponseCreateDto, Exception]:
    try:
        # Query untuk mengambil wishlist berdasarkan user_id dengan pagination
        courier_model = db.execute(
            select(CourierModel)
            .where(CourierModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not courier_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"All data courier from this user ID : {user_id} not found"
                ).dict()
            )


        # Konversi wishlist menjadi DTO
        courier_dto = [
            courier_dtos.CourierInfoDto(
            id=courier.id,
            courier_name=courier.courier_name,
            phone_number=courier.phone_number,
            service_type=courier.service_type,
            weight=courier.weight,
            length=courier.length,
            width=courier.width,
            height=courier.height,
            cost=courier.cost,
            estimated_delivery=courier.estimated_delivery,
            is_active=courier.is_active,
            created_at=courier.created_at
        )
            for courier in courier_model
        ]

        # Return DTO dengan respons yang telah dibangun
        return build(data=courier_dtos.AllCourierListResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message=f"All data courier from user ID {user_id} accessed successfully",
            data=courier_dto
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
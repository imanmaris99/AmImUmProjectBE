from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

from typing import List, Type

from app.models.shipment_address_model import ShipmentAddressModel
from app.dtos import shipment_address_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.utils.result import build, Result

def my_shipping_address(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 10
    ) -> Result[shipment_address_dtos.AllAddressListResponseDto, Exception]:
    try:
        address_model = db.execute(
            select(ShipmentAddressModel)
            .where(ShipmentAddressModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not address_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"All data shipping address from this user ID : {user_id} not found"
                ).dict()
            )

        # Konversi wishlist menjadi DTO
        address_dto = [
            shipment_address_dtos.ShipmentAddressInfoDto(
            id=address.id,
            name=address.name,
            phone=address.phone,
            address=address.address,
            city=address.city,
            city_id=address.city_id,
            state=address.state,
            country=address.country,
            zip_code=address.zip_code,
            created_at=address.created_at
        )
            for address in address_model
        ]

        # Return DTO dengan respons yang telah dibangun
        return build(data=shipment_address_dtos.AllAddressListResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"All data shipping address from user ID {user_id} accessed successfully",
            data=address_dto
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
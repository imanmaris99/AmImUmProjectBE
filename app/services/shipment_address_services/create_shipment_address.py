from datetime import datetime
from fastapi import HTTPException, status

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.shipment_address_model import ShipmentAddressModel
from app.dtos import shipment_address_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.utils.result import build, Result


def create_shipment_address(
        request_data: shipment_address_dtos.ShipmentAddressCreateDto, 
        user_id: str,
        db: Session
    ) -> Result[shipment_address_dtos.ShipmentAddressResponseDto, Exception]:
    try:
        shipment_address = ShipmentAddressModel(
            name=request_data.name,
            phone=request_data.phone,
            address=request_data.address,
            city=request_data.city,
            state=request_data.state,
            country=request_data.country,
            zip_code=request_data.zip_code,
            customer_id=user_id
        )

        db.add(shipment_address)
        db.commit()
        db.refresh(shipment_address)

        # Buat DTO response
        address_response = shipment_address_dtos.ShipmentAddressInfoDto(
            id=shipment_address.id,
            name=shipment_address.name,
            phone=shipment_address.phone,
            address=shipment_address.address,
            city=shipment_address.city,
            state=shipment_address.state,
            country=shipment_address.country,
            zip_code=shipment_address.zip_code,
            created_at=shipment_address.created_at
        )

        return build(data=shipment_address_dtos.ShipmentAddressResponseDto(
            status_code=201,
            message="Your data of shipment address has been saved in db",
            data=address_response
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
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


from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_address_model import ShipmentAddressModel
from app.dtos import shipment_address_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result


def delete_address(
        db: Session, 
        request_delete: shipment_address_dtos.DeleteAddressDto,
        user_id: str
        ) -> Result[None, Exception]:
    try:
        address_model = db.execute(
            select(ShipmentAddressModel)
            .where(
                ShipmentAddressModel.id == request_delete.address_id,
                ShipmentAddressModel.customer_id == user_id
            )  
        ).scalars().first()

        if not address_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Shipment address data with ID : {request_delete.address_id} not found"
                ).dict()
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        address_delete_info = shipment_address_dtos.DeleteAddressInfoDto(
            address_id=address_model.id,
            name=address_model.name,
            phone=address_model.phone,
            address=address_model.address
        )

        db.delete(address_model)
        db.commit()

        return build(data=shipment_address_dtos.DeleteAddressResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Your data of Shipment address with ID {request_delete.address_id} has been deleted",
            data=address_delete_info
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

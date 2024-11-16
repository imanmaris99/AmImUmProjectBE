
from typing import Type

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_address_model import ShipmentAddressModel
from app.dtos import shipment_address_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result

def update_shipment_address(
        db: Session, 
        update_request: shipment_address_dtos.ShipmentAddressIdToUpdateDto,
        address_data: shipment_address_dtos.ShipmentAddressCreateDto,
        user_id: str
        ) -> Result[Type[ShipmentAddressModel], Exception]:
    try:
        address_model = db.execute(
            select(ShipmentAddressModel)
            .where(
                ShipmentAddressModel.id == update_request.address_id,
                ShipmentAddressModel.customer_id == user_id
            )  
        ).scalars().first()
        
        if not address_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Data of Address with ID {update_request.address_id} in User ID {user_id} Not Found"
                ).dict()
            ))
        
        for attr, value in address_data.model_dump().items():
            setattr(address_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(address_model)

        return build(data=shipment_address_dtos.ShipmentAddressResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Updated data Address with ID {update_request.address_id} has been success",
            data=shipment_address_dtos.ShipmentAddressInfoDto(
                id=address_model.id,
                name=address_model.name,
                phone=address_model.phone,
                address=address_model.address,
                city=address_model.city,
                state=address_model.state,
                country=address_model.country,
                zip_code=address_model.zip_code,
                created_at=address_model.created_at
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
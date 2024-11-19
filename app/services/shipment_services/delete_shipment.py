from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_model import ShipmentModel
from app.dtos import shipment_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.utils.error_parser import find_errr_from_args
from app.utils.result import build, Result


def delete_shipment(
        db: Session, 
        request_delete: shipment_dtos.ShipmentIdToUpdateDto,
        user_id: str
        ) -> Result[None, Exception]:
    try:
        shipment_model = db.execute(
            select(ShipmentModel)
            .where(
                ShipmentModel.id == request_delete.shipment_id,
                ShipmentModel.customer_id == user_id
            )  
        ).scalars().first()

        if not shipment_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Shipment data with shipment ID : {request_delete.shipment_id} not found"
                ).dict()
            ))
        
        # Simpan informasi pengguna sebelum dihapus
        shipment_delete_info = shipment_dtos.DeleteShipmentInfoDto(
            id=shipment_model.id,
            my_address=shipment_model.my_address,
            my_courier=shipment_model.my_courier,
            created_at=shipment_model.created_at
        )

        db.delete(shipment_model)
        db.commit()

        return build(data=shipment_dtos.DeleteShipmentInfoResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Your one data of Shipment with ID {request_delete.shipment_id} has been deleted",
            data=shipment_delete_info
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

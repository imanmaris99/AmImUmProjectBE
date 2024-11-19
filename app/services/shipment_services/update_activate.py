from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_model import ShipmentModel
from app.dtos import shipment_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import get_cart_item, handle_db_error
from app.utils.result import build, Result

# Fungsi untuk Mengupdate Status Aktif Item
def update_activate(
        db: Session, 
        update_request: shipment_dtos.ShipmentIdToUpdateDto,
        activate_update: shipment_dtos.UpdateActivateDto,
        user_id: str
        ) -> Result[Type[ShipmentModel], Exception]:
    try:
        activate_model = db.execute(
            select(ShipmentModel)
            .where(
                ShipmentModel.id == update_request.shipment_id,
                ShipmentModel.customer_id == user_id
            )  
        ).scalars().first()             

        if not activate_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Shipment information from this Shipment ID {update_request.shipment_id} Not Found"
                ).dict()
            ))

        # Update atribut berdasarkan input dari DTO
        for attr, value in activate_update.model_dump().items():
            setattr(activate_model, attr, value)

        # Simpan perubahan ke dalam database   
        db.commit()
        db.refresh(activate_model)

        return build(data=shipment_dtos.ShipmentActivateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Updated Info activation from this Shipment ID {update_request.shipment_id} has been success",
            data=shipment_dtos.ShipmentInfoDto(
                shipment_id=activate_model.id,
                courier_id=activate_model.courier_id,
                address_id=activate_model.address_id,
                code_tracking=activate_model.code_tracking,
                created_at=activate_model.created_at,
                is_active=activate_model.is_active
            )
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

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

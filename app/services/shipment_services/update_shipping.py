from typing import Type
from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_model import ShipmentModel
from app.dtos import shipment_address_dtos, shipment_dtos, courier_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.courier_services import update_courier_data
from app.services.shipment_address_services import update_shipment_address

from app.utils.result import build, Result


def update_shipping(
        db: Session,
        update_request: shipment_dtos.ShipmentIdToUpdateDto,
        request: shipment_dtos.RequestIdToUpdateDto,
        update_data: shipment_dtos.ShipmentCreateDto,
        user_id: str
) -> Result[Type[ShipmentModel], Exception]:
    try:
        # Cari model pengiriman berdasarkan shipment_id dan user_id
        shipment_model = db.execute(
            select(ShipmentModel)
            .filter(
                ShipmentModel.id == update_request.shipment_id,
                ShipmentModel.address_id == request.address_id,
                ShipmentModel.courier_id == request.courier_id,
                ShipmentModel.customer_id == user_id
            )
        ).scalars().first()

        if not shipment_model:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Shipment with ID {update_request.shipment_id} for User ID {user_id} not found."
                ).dict()
            ))

        # Cek dan update alamat jika ada perubahan
        if update_data.address:
            address_response = update_shipment_address(
                db=db,
                update_request=shipment_address_dtos.ShipmentAddressIdToUpdateDto(
                    address_id=request.address_id
                ),
                address_data=update_data.address,
                user_id=user_id
            )
            if address_response.error:
                return build(error=address_response.error)

        # Cek dan update kurir jika ada perubahan
        if update_data.courier:
            courier_response = update_courier_data(
                db=db,
                courier_update=courier_dtos.CourierIdToUpdateDto(
                    courier_id=request.courier_id
                ),
                weight_data=update_data.courier,
                user_id=user_id
            )
            if courier_response.error:
                return build(error=courier_response.error)

        # Update data pengiriman lainnya
        for attr, value in update_data.model_dump().items():
            if value is not None:  # Menghindari pembaruan dengan nilai None
                setattr(shipment_model, attr, value)

        # Commit perubahan ke database
        db.commit()
        db.refresh(shipment_model)

        return build(data=shipment_dtos.MyShipmentUpdateResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Shipment with ID {update_request.shipment_id} has been successfully updated.",
            data=shipment_dtos.MyShipmentInfoDto(
                id=shipment_model.id,
                my_address=shipment_model.my_address,
                my_courier=shipment_model.my_courier,
                is_active=shipment_model.is_active,
                created_at=shipment_model.created_at
            )
        ))

    except SQLAlchemyError as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))

    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

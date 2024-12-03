from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_model import ShipmentModel
from app.models.courier_model import CourierModel
from app.models.shipment_address_model import ShipmentAddressModel

from app.dtos import shipment_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.services.courier_services import process_shipping_cost
from app.services.shipment_address_services import create_shipment_address

from app.utils.result import build, Result


def new_post(
    request_data: shipment_dtos.RequestIdToUpdateDto, 
    user_id: str, 
    db: Session
) -> Result[shipment_dtos.ShipmentResponseDto, Exception]:
    try:
        # Validasi awal
        if not request_data.courier_id or not request_data.address_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Courier ID and Address ID must be provided."
                ).dict()
            )

        # Query courier
        courier_model = db.execute(
            select(CourierModel)
            .where(
                CourierModel.id == request_data.courier_id,
                CourierModel.customer_id == user_id
            )
        ).scalars().first()
        if not courier_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Courier with ID {request_data.courier_id} for user ID {user_id} not found."
                ).dict()
            )

        # Query address
        address_model = db.execute(
            select(ShipmentAddressModel)
            .where(
                ShipmentAddressModel.id == request_data.address_id,
                ShipmentAddressModel.customer_id == user_id
            )
        ).scalars().first()
        if not address_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Address with ID {request_data.address_id} for user ID {user_id} not found."
                ).dict()
            )

        # Buat Shipment
        with db.begin():  # Transaksi aman
            shipment = ShipmentModel(
                code_tracking="in process",
                courier_id=request_data.courier_id,
                address_id=request_data.address_id,
                is_active=True
            )
            db.add(shipment)
            db.flush()  # Simpan ke database tanpa commit
            db.refresh(shipment)

        # Buat DTO Response
        shipment_response = shipment_dtos.ShipmentInfoDto(
            **shipment.dict()
        )

        return build(data=shipment_dtos.ShipmentResponseDto(
            status_code=201,
            message="Your data of shipment has been saved in db",
            data=shipment_response
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        return build(error=http_ex)

    except Exception as e:
        db.rollback()
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))

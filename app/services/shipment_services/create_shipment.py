from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.shipment_model import ShipmentModel
from app.dtos import shipment_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error
from app.services.courier_services import process_shipping_cost
from app.services.shipment_address_services import create_shipment_address

from app.utils.result import build, Result


def _has_valid_city_id(city_id) -> bool:
    try:
        return int(city_id or 0) > 0
    except (TypeError, ValueError):
        return False


def _invalid_city_id_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorResponseDto(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Bad Request",
            message="Shipment address city_id must be selected from RajaOngkir before checkout."
        ).dict()
    )


def create_shipment(
    request_data: shipment_dtos.ShipmentCreateDto, 
    user_id: str, 
    db: Session
) -> Result[shipment_dtos.ShipmentResponseDto, Exception]:
    try:
        if not _has_valid_city_id(getattr(request_data.address, "city_id", None)):
            return build(error=_invalid_city_id_error())

        # 1. Membuat Shipment Address
        address_response = create_shipment_address(request_data.address, user_id, db)
        if address_response.error:
            return build(error=address_response.error)
        
        address_id = address_response.data.data.id

        # 2. Membuat Courier
        courier_response = process_shipping_cost(request_data.courier, user_id, db)
        if courier_response.error:
            return build(error=courier_response.error)
        
        courier_id = courier_response.data.data.id

        # 3. Membuat Shipment aktif untuk user ini.
        # Checkout membaca shipment aktif berdasarkan customer_id, jadi pastikan
        # shipment baru terikat ke user dan shipment lama dinonaktifkan.
        db.query(ShipmentModel).filter(
            ShipmentModel.customer_id == user_id,
            ShipmentModel.is_active == True
        ).update({ShipmentModel.is_active: False}, synchronize_session=False)

        shipment = ShipmentModel(
            code_tracking="in process",
            courier_id=courier_id,
            address_id=address_id,
            customer_id=user_id,
            is_active=True
        )

        db.add(shipment)
        db.commit()
        db.refresh(shipment)

        # Buat DTO response
        shipment_response = shipment_dtos.ShipmentInfoDto(
            shipment_id=shipment.id,
            courier_id=shipment.courier_id,
            address_id=shipment.address_id,
            code_tracking=shipment.code_tracking,
            created_at=shipment.created_at,
            is_active=shipment.is_active
        )

        return build(data=shipment_dtos.ShipmentResponseDto(
            status_code=201,
            message="Your data of shipment has been saved in db",
            data=shipment_response
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

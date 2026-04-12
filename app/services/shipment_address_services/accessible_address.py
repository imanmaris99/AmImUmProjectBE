from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

import json
import logging

from app.models.shipment_address_model import ShipmentAddressModel
from app.models.user_model import UserModel
from app.dtos import shipment_address_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

OWNER_SHOP_ID = "9d899cc1-ec4e-4f54-9e3d-89502657db91"  # Constant ID for shop owner
logger = logging.getLogger(__name__)
CACHE_TTL = 3600
RESPONSE_MESSAGE = "Origin address accessed successfully"

def get_target_user_role(
        db: Session, 
        target_user_id: str
    ) -> str:
    """
    Mengambil role user target.
    """
    return db.execute(
        select(UserModel.role)
        .where(UserModel.id == target_user_id)
    ).scalar_one_or_none()

def get_shipment_address(
        db: Session, 
        customer_id: str
    ) -> ShipmentAddressModel:
    """
    Mengambil alamat pengiriman berdasarkan customer_id.
    """
    return db.execute(
        select(ShipmentAddressModel)
        .where(ShipmentAddressModel.customer_id == customer_id)
    ).scalars().first()

def handle_not_found_error(message: str):
    """
    Menangani error 'not found' untuk alamat yang tidak ditemukan.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorResponseDto(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message=message
        ).dict()
    )

def accessible_address(
    db: Session, 
    user_id: str,  
    target_user_id: str
) -> Result[shipment_address_dtos.ShipmentAddressResponseDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"origin_address:{target_user_id}"

        # Check if product data exists in Redis
        cached_origin = None
        if redis_client:
            try:
                cached_origin = redis_client.get(redis_key)
            except Exception as cache_error:
                logger.warning("Failed to read accessible address cache for key %s: %s", redis_key, cache_error)
        if cached_origin:
            address_dto = shipment_address_dtos.ShipmentAddressInfoDto(**json.loads(cached_origin))
            return build(data=shipment_address_dtos.ShipmentAddressResponseDto(
                status_code=200,
                message=RESPONSE_MESSAGE,
                data=address_dto
            ))
        
        if target_user_id == OWNER_SHOP_ID:
            address_model = get_shipment_address(db, target_user_id)
        else:
            target_user_role = get_target_user_role(db, target_user_id)

            if not target_user_role:
                handle_not_found_error(f"User with ID {target_user_id} not found")

            if target_user_role == 'pemilik_toko' or user_id == target_user_id:
                address_model = get_shipment_address(db, target_user_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_403_FORBIDDEN,
                        error="Forbidden",
                        message=f"User with ID {user_id} is not authorized to access this address"
                    ).dict()
                )

        if not address_model:
            handle_not_found_error(f"Shipping address for user ID {target_user_id} not found")

        # Convert model to DTO
        address_dto = shipment_address_dtos.ShipmentAddressInfoDto(
            id=address_model.id,
            name=address_model.name,
            phone=address_model.phone,
            address=address_model.address,
            city=address_model.city,
            city_id=address_model.city_id,
            state=address_model.state,
            country=address_model.country,
            zip_code=address_model.zip_code,
            created_at=address_model.created_at
        )

        if redis_client:
            try:
                redis_client.setex(redis_key, CACHE_TTL, json.dumps(address_dto.dict(), default=custom_json_serializer))
            except Exception as cache_error:
                logger.warning("Failed to write accessible address cache for key %s: %s", redis_key, cache_error)

        return build(data=shipment_address_dtos.ShipmentAddressResponseDto(
            status_code=status.HTTP_200_OK,
            message=RESPONSE_MESSAGE,
            data=address_dto
        ))

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
        return build(error=handle_db_error(db, e))

    except HTTPException as http_ex:
        return build(error=http_ex)

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
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"            
            ).dict()
        ))

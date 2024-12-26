from fastapi import HTTPException, status

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError

import json

from app.models.shipment_address_model import ShipmentAddressModel
from app.dtos import shipment_address_dtos
from app.dtos.error_response_dtos import ErrorResponseDto

from app.services.cart_services.support_function import handle_db_error

from app.utils.result import build, Result
from app.libs.redis_config import custom_json_serializer, redis_client

CACHE_TTL = 3600

def my_shipping_address(
        db: Session, 
        user_id: str,  
        skip: int = 0, 
        limit: int = 100
    ) -> Result[shipment_address_dtos.AllAddressListResponseDto, Exception]:
    try:
        # Redis key for caching
        redis_key = f"origin_address:{user_id}:{skip}:{limit}"

        # Check if address data exists in Redis
        cached_address = redis_client.get(redis_key)
        if cached_address:
            address_dto = [
                shipment_address_dtos.ShipmentAddressInfoDto(**addr)
                for addr in json.loads(cached_address)
            ]
            return build(data=shipment_address_dtos.AllAddressListResponseDto(
                status_code=status.HTTP_200_OK,
                message="Details info Destination Address successfully retrieved (from cache)",
                data=address_dto
            ))

        # Query database
        address_model = db.execute(
            select(ShipmentAddressModel)
            .where(ShipmentAddressModel.customer_id == user_id)
            .offset(skip)
            .limit(limit)
        ).scalars().all()

        if not address_model:
            return build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"All data shipping address from this user ID : {user_id} not found"
                ).dict()
            ))

        # Convert model to DTO
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

        # Cache the data in Redis
        redis_client.setex(redis_key, CACHE_TTL, json.dumps(
            [dto.dict() for dto in address_dto], 
            default=custom_json_serializer
        ))

        # Return the response DTO
        return build(data=shipment_address_dtos.AllAddressListResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"All data shipping address from user ID {user_id} accessed successfully",
            data=address_dto
        ))

    except IntegrityError as ie:
        return build(error=HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database integrity error: {str(ie)}"
            ).dict()
        ))

    except DataError as de:
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
        return build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

from fastapi import APIRouter, Depends, status

from typing import List, Annotated

from sqlalchemy.orm import Session

from app.dtos import shipment_address_dtos
from app.services import shipment_address_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/shipment-address",
    tags=["Address Shipping"]
)

@router.post(
        "/create",
        status_code=status.HTTP_201_CREATED,
        response_model=shipment_address_dtos.ShipmentAddressResponseDto,
        summary="Post Info Address Shipping to Database"

    )
def save_shipping_address(
    request_data: shipment_address_dtos.ShipmentAddressCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = shipment_address_services.create_shipment_address(
        request_data, 
        jwt_token.id,
        db
    )
    
    if result.error:
        raise result.error
    
    return result.unwrap()
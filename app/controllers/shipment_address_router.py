from fastapi import APIRouter, Depends, status

from typing import List, Annotated, Optional

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


@router.get(
    "/my-address",
    response_model=shipment_address_dtos.AllAddressListResponseDto,
    status_code=status.HTTP_200_OK,
    summary="Get all data shipping address in my account"
)
async def get_my_shipping_address(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = shipment_address_services.my_shipping_address(
        db, 
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
    "/address/pemilik-toko",
    response_model=shipment_address_dtos.ShipmentAddressResponseDto,
    status_code=status.HTTP_200_OK,
    summary="Get shipping address of the store owner (accessible by all users)"
)
async def get_store_owner_address(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    Endpoint ini secara otomatis menampilkan alamat dari pemilik toko dengan ID tertentu,
    tanpa memerlukan input ID pemilik toko dalam URL. Semua user yang login dapat mengakses
    alamat ini.
    """
    result = shipment_address_services.accessible_address(
        db=db,
        user_id=jwt_token.id,  # ID user yang sedang melakukan request (dari JWT)
        target_user_id="9d899cc1-ec4e-4f54-9e3d-89502657db91"  # Hardcode ID pemilik toko
    )

    if result.error:
        raise result.error
    
    return result.unwrap()
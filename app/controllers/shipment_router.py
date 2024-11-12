from fastapi import APIRouter, Depends, status
from typing import Annotated
from sqlalchemy.orm import Session

from app.dtos import shipment_dtos
from app.services.shipment_services import create_shipment
from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service


router = APIRouter(
    prefix="/shipment",
    tags=["Shipment Information"]
)

@router.post(
    "/create-shipment",
    response_model=shipment_dtos.ShipmentResponseDto,
    status_code=status.HTTP_201_CREATED,  # Menyatakan bahwa ini resource creation
)
def create_shipment_route(
    request_data: shipment_dtos.ShipmentCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    # Panggil fungsi service untuk membuat shipment
    result = create_shipment(
        request_data=request_data, 
        user_id=jwt_token.id, 
        db=db
    )

    if result.error:
        raise result.error

    return result.unwrap()

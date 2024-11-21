from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.services import order_services
from app.dtos import order_dtos

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)

@router.post(
        "/create", 
        response_model=order_dtos.OrderInfoResponseDto,
        status_code=status.HTTP_201_CREATED
    )
def create_order(
    order_dto: order_dtos.OrderCreateDTO,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    # Memanggil service untuk menambahkan item ke dalam cart
    result = order_services.create_order(
        db, 
        order_dto, 
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/my-orders",
    response_model=order_dtos.GetOrderInfoResponseDto,
    status_code=status.HTTP_200_OK,
    summary="Get all orders by account login"
)
async def get_my_order(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = order_services.my_order(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()

from fastapi import APIRouter, Depends, status

from typing import List, Annotated

from sqlalchemy.orm import Session

from app.dtos import courier_dtos
from app.services import courier_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/courier",
    tags=["Courier Shipping"]
)

@router.post(
        "/shipping-cost",
        status_code=status.HTTP_201_CREATED,
        response_model=courier_dtos.CourierResponseDto,
        summary="Post Data of Courier to Database"

    )
def get_and_save_shipping_cost(
    request_data: courier_dtos.CourierCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = courier_services.process_shipping_cost(
        request_data, 
        jwt_token.id,
        db
    )
    
    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/my-courier",
    response_model=courier_dtos.AllCourierListResponseCreateDto,
    status_code=status.HTTP_200_OK,
    summary="Get all data courier in my account"
)
async def get_my_courier(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = courier_services.my_courier(
        db, 
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.put(
        "/edit-service/{courier_id}", 
        response_model=courier_dtos.CourierInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK
    )
def update_my_courier_service(
        courier_update: courier_dtos.CourierIdToUpdateDto,
        courier_data: courier_dtos.CourierDataUpdateDTO,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = courier_services.update_courier(
        db, 
        courier_update, 
        courier_data, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.put(
        "/edit-courier/{courier_id}", 
        response_model=courier_dtos.CourierInfoUpdateWeightResponseDto,
        status_code=status.HTTP_200_OK
    )
def update_my_courier(
        courier_update: courier_dtos.CourierIdToUpdateDto,
        weight_data: courier_dtos.CourierDataWeightUpdateDTO,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = courier_services.update_weight(
        db, 
        courier_update, 
        weight_data, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()
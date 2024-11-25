from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.services import payment_services
from app.dtos import payment_dtos

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "/create",
    response_model=payment_dtos.PaymentInfoResponseDto,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    payment_data: payment_dtos.PaymentCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = payment_services.create_transaction(
        db,
        payment_data, 
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.post(
    "/notifications",
    response_model=payment_dtos.PaymentNotificationResponseDto,
    status_code=status.HTTP_200_OK
)
def receive_payment_notification(
    notification_data: payment_dtos.InfoTransactionIdDto,  # Data dari body request
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    Endpoint untuk menerima notifikasi pembayaran dari Midtrans.

    Args:
        notification_data (InfoTransactionIdDto): Data notifikasi yang dikirimkan oleh Midtrans.
        db (Session): Sesi database yang digunakan.

    Returns:
        PaymentNotificationResponseDto: Respons sukses atau error.
    """
    result = payment_services.handle_notification(
        notification_data, 
        db,
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()

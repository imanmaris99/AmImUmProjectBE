from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import cart_dtos
from app.services import cart_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)


@router.post(
    "/product/{product_id}/{variant_id}",
    response_model=cart_dtos.CartResponseCreateDto,
    status_code=status.HTTP_201_CREATED,
)
def post_my_item_of_cart(
    cart: cart_dtos.CartCreateOfIdProductDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    # Buat DTO input dari parameter router
    cart_create_dto = cart_dtos.CartCreateOfIdProductDto(
        product_id=cart.product_id,
        variant_id=cart.variant_id
    )

    # Memanggil service untuk menambahkan item ke dalam cart
    result = cart_services.post_item(
        db, 
        cart_create_dto, 
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()
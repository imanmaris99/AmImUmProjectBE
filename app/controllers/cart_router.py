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


@router.get(
    "/my-cart",
    response_model=cart_dtos.AllCartResponseCreateDto,
    status_code=status.HTTP_200_OK,
)
async def get_my_cart(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    result = cart_services.my_cart(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.put(
        "/edit-quantity/{cart_id}", 
        response_model=cart_dtos.CartInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK
    )
def update_my_quantity_item(
        cart: cart_dtos.UpdateByIdCartDto,
        quantity_update: cart_dtos.UpdateQuantityItemDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = cart_services.update_quantity_item(
        db, 
        cart=cart, 
        quantity_update=quantity_update, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.data

@router.put(
        "/edit-activate/{cart_id}", 
        response_model=cart_dtos.CartInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK
    )
def update_my_activate_item(
        cart: cart_dtos.UpdateByIdCartDto,
        activate_update: cart_dtos.UpdateActivateItemDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = cart_services.update_activate_item(
        db, 
        cart=cart, 
        activate_update=activate_update, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.data


@router.delete(
        "/delete/{cart_id}",
        response_model=cart_dtos.DeleteCartResponseDto,
        status_code=status.HTTP_200_OK
    )
def delete_my_item_cart(
        cart: cart_dtos.DeleteByIdCartDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = cart_services.delete_item(
        db, 
        cart=cart, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()
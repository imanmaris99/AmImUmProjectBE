from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import product_dtos
from app.services import product_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/product",
    tags=["Product"]
)

@router.post(
        "/", 
        response_model=product_dtos.ProductResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def create_product(
    create_product: product_dtos.ProductCreateDTO, 
    db: Session = Depends(get_db),
):
    result = product_services.create_product(
        db, 
        create_product
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
        "/", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def read_all_products(   
    db: Session = Depends(get_db)
):
    result = product_services.all_product(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

# get-list-product-by-keyword-search
@router.get(
        "/{product_name}", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def search_product(
        product_name: str,
        # jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = product_services.search_product(
        db,
        product_name
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
        "/discount", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def read_all_products_with_discount(   
    db: Session = Depends(get_db)
):
    result = product_services.all_product_with_discount(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/production/{production_id}", 
    response_model=List[product_dtos.AllProductInfoDTO]
)
def read_all_products_by_id_production(
    production_id: int,  # Ambil production_id dari path
    db: Session = Depends(get_db)
):
    # Langsung kirim production_id ke service tanpa DTO
    result = product_services.all_product_by_id_production(
        db=db,
        production_id=production_id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


# get-product-discount-by-keyword-search
@router.get(
        "/discount/{product_name}", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def search_product_discount(
        product_name: str,
        # jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    result = product_services.search_product_discount(
        db,
        product_name
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/discount/{production_id}", 
    response_model=List[product_dtos.AllProductInfoDTO]
)
def read_all_products_discount_by_id_production(
    production_id: int,  # Ambil production_id dari path
    db: Session = Depends(get_db)
):
    # Langsung kirim production_id ke service tanpa DTO
    result = product_services.all_discount_by_id_production(
        db=db,
        production_id=production_id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get("/detail/{product_id}", response_model=product_dtos.ProductDetailResponseDto)
def get_product_detail(product_id: UUID, db: Session = Depends(get_db)):
    # Call the service to get the product detail
    result = product_services.get_product_by_id(db, product_id)

    if result.error:
        raise result.error
    # Unwrap the result to raise exceptions if they exist, otherwise return the data
    return result.unwrap()





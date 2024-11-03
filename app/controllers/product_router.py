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
        "/discount/all", 
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

@router.get(
    "/production/loader/{production_id}",
    response_model=product_dtos.ProductListScrollResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Daftar produk berhasil diambil dengan format respons infinite scrolling",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                            "id": "2762403f-2eb1-4c94-b4af-05c04759fcc0",
                            "name": "Buyung Upik",
                            "price": 8000,
                            "all_variants": [
                                {
                                "id": 2,
                                "variant": "Cokelat",
                                "img": "https://5e4da772-e77b-4889-8314-7b9930a13c71_1729515706_buyung-upik-c-min.png?",
                                "discount": 10,
                                "discounted_price": 7200,
                                "updated_at": "2024-10-21T13:01:38.381228Z"
                                },
                                                                {
                                "id": 3,
                                "variant": "Strawberry",
                                "img": "https://5e4da772-e77b-4889-8314-7b9930a13c71_1729515706_buyung-upik-c-min.png?",
                                "discount": 0,
                                "discounted_price": 8000,
                                "updated_at": "2024-10-21T13:01:38.381228Z"
                                }
                            ],
                            "created_at": "2024-10-21T12:36:09.928091Z"
                            },
                            {
                            "id": "3762504f-2eb1-4c94-b4af-05c04759fcc1",
                            "name": "Pegel Linu",
                            "price": 9000,
                            "all_variants": [
                                {
                                "id": 1,
                                "variant": "Original",
                                "img": "https://5e4da772-e77b-4889-8314-7b9930a13c71_1729515706_buyung-upik-c-min.png?",
                                "discount": 0,
                                "discounted_price": 9000,
                                "updated_at": "2024-10-21T13:01:38.381228Z"
                                }
                            ],
                            "created_at": "2024-10-21T12:36:09.928091Z"
                            }
                        ],
                        "has_more": False
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Data produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "No information about products found."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Konflik saat mengambil data produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Database conflict occurred while fetching data."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while fetching data."
                    }
                }
            }
        }
    },
    summary="Fetch a infinite scrolling list of products by id production"
)
def get_list_products_by_id_production(
    production_id: int,
    skip: int = 0,               # Posisi awal data untuk pagination
    limit: int = 6,              # Jumlah data yang akan ditampilkan per halaman
    db: Session = Depends(get_db)
):
    """
    # Menampilkan List Produk dari Brand dengan Pagination #

    Endpoint ini memungkinkan pengguna untuk Mengambil daftar item produksi dengan menggunakan paginasi.

    **Parameter:**
    - **production_id** (int): ID dari produsen untuk filter list produk.
    - **skip** (int, opsional): Jumlah item yang dilewati sebelum memulai pengambilan data. Default adalah 0.
    - **limit** (int, opsional): Jumlah maksimum item yang akan dikembalikan dalam respons. Default adalah 6.
    
    **Return:**
    - **200 OK**: Daftar item produk dari brand produksi beserta metadata paginasi (remaining records, `has_more`).
    - **404 Not Found**: Jika tidak ada item produk dari id produsen yang ditemukan.
    - **409 Conflict**: Jika terjadi kesalahan pada database.
    - **500 Internal Server Error**: Jika terjadi kesalahan yang tidak terduga.

    """
    result = product_services.infinite_scrolling_list_products_by_id_production(
        db, 
        production_id=production_id,
        skip=skip, 
        limit=limit
    )

    if result.error:
        raise result.error  
    
    return result.unwrap()


@router.get(
        "/production/{production_id}/{product_name}", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def search_product_from_filtering_of_id_production(
        production_id: int,
        product_name: str,
        db: Session = Depends(get_db)
):
    result = product_services.search_product_of_id_production(
        db,
        production_id,
        product_name
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

# get-product-discount-by-keyword-search
@router.get(
        "/discount/name/{product_name}", 
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
    "/discount/production/{production_id}", 
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

@router.get(
        "/detail/{product_id}", 
        response_model=product_dtos.ProductDetailResponseDto
    )
def get_product_detail(product_id: UUID, db: Session = Depends(get_db)):
    # Call the service to get the product detail
    result = product_services.get_product_by_id(db, product_id)

    if result.error:
        raise result.error
    # Unwrap the result to raise exceptions if they exist, otherwise return the data
    return result.unwrap()


@router.put(
    "/{product_id}",
    response_model=product_dtos.ProductResponseDto,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(jwt_service.admin_access_required)]  # Pastikan Anda memiliki dependency untuk akses admin
)
def update_product(
    product_id_update: product_dtos.ProductIdToUpdateDTO, 
    product_update: product_dtos.ProductUpdateDTO,
    db: Session = Depends(get_db)
):
    result = product_services.update_product(
        db=db, 
        product_id_update=product_id_update, 
        product_update=product_update  
    )

    if result.error:
        raise result.error

    return result.unwrap()

@router.delete(
        "/delete/{product_id}", 
        response_model= product_dtos.DeleteProductResponseDto,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def delete_product(
    product_data: product_dtos.DeleteByIdProductDto, 
    db: Session = Depends(get_db)
):
    result = product_services.delete_product(
        db, 
        product_data=product_data)
    
    if result.error:
        raise result.error
    
    return result.unwrap()


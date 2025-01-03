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
        "/create", 
        response_model=product_dtos.ProductResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)],
        responses={
            status.HTTP_201_CREATED: {
                "description": "Produk berhasil dibuat",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 201,
                            "message": "Successfully created new product",
                            "data": {
                                "id": "PROD-20241106001",
                                "name": "Herbal Supplement",
                                "description": "A product for daily health...",
                                "price": 50000,
                                "stock": 100,
                                "created_at": "2024-11-06T12:00:00",
                            }
                        }
                    }
                }
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Data yang diberikan tidak valid atau ada field yang hilang",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 400,
                            "error": "Bad Request",
                            "message": "Data produk yang diberikan tidak valid. Periksa kembali input Anda."
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Token tidak valid atau pengguna tidak memiliki akses",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Token tidak valid atau pengguna tidak memiliki akses."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat membuat produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat membuat produk."
                        }
                    }
                }
            }
        },
        summary="Create a new product"
    )
def create_product(
    create_product: product_dtos.ProductCreateDTO, 
    db: Session = Depends(get_db),
):
    """
    # Buat Produk Baru #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk membuat produk baru.
    
    **Parameter:**
    - **create_product** (ProductCreateDTO): Data produk baru yang akan dibuat.

    **Return:**
    - **201 Created**: Produk berhasil dibuat.
    - **400 Bad Request**: Jika ada kesalahan input data atau field yang hilang.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **500 Internal Server Error**: Kesalahan server saat membuat produk.
    
    """
    result = product_services.create_product(
        db, 
        create_product
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
        "/all", 
        response_model=product_dtos.AllProductInfoResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Daftar semua produk berhasil diambil",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully retrieved all products",
                            "data": [
                                {
                                    "id": "PROD-20241106001",
                                    "name": "Herbal Supplement",
                                    "description": "A product for daily health...",
                                    "price": 50000,
                                    "stock": 100,
                                    "highest_promo": 15.0,
                                    "avg_rating": 4.5
                                },
                                {
                                    "id": "PROD-20241106002",
                                    "name": "Vitamin C 1000mg",
                                    "description": "Supports immune health...",
                                    "price": 75000,
                                    "stock": 200,
                                    "highest_promo": 10.0,
                                    "avg_rating": 4.8
                                }
                            ]
                        }
                    }
                }
            },
            status.HTTP_204_NO_CONTENT: {
                "description": "Tidak ada produk yang tersedia",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 204,
                            "message": "No products available."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mengambil daftar produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mengambil daftar produk."
                        }
                    }
                }
            }
        },
        summary="Get all products"
    )
def read_all_products(   
    db: Session = Depends(get_db)
):
    """
    # Ambil Semua Produk #

    Endpoint ini memungkinkan pengguna untuk mengambil semua produk yang tersedia di dalam database.
    
    **Return:**
    - **200 OK**: Daftar semua produk berhasil diambil.
    - **204 No Content**: Tidak ada produk yang tersedia untuk ditampilkan.
    - **500 Internal Server Error**: Kesalahan server saat mengambil daftar produk.
    """
    result = product_services.all_product(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

# get-list-product-by-keyword-search
@router.get(
        "/{product_name}", 
        response_model=product_dtos.AllProductInfoResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Produk ditemukan berdasarkan nama",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully found products",
                            "data": [
                                {
                                    "id": "PROD-20241106001",
                                    "name": "Herbal Supplement",
                                    "description": "A product for daily health...",
                                    "price": 50000,
                                    "stock": 100,
                                    "highest_promo": 15.0,
                                    "avg_rating": 4.5
                                },
                                {
                                    "id": "PROD-20241106002",
                                    "name": "Vitamin C 1000mg",
                                    "description": "Supports immune health...",
                                    "price": 75000,
                                    "stock": 200,
                                    "highest_promo": 10.0,
                                    "avg_rating": 4.8
                                }
                            ]
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Produk tidak ditemukan berdasarkan nama",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Tidak ada produk yang ditemukan dengan nama tersebut."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mencari produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mencari produk."
                        }
                    }
                }
            }
        },
        summary="Search for products by name"
    )
def search_product(
        product_name: str,
        db: Session = Depends(get_db)
):
    """
    # Cari Produk Berdasarkan Nama #

    Endpoint ini memungkinkan pengguna untuk mencari produk berdasarkan nama yang diberikan.
    
    **Parameter:**
    - **product_name** (str): Nama produk yang akan dicari.

    **Return:**
    - **200 OK**: Produk ditemukan berdasarkan nama.
    - **404 Not Found**: Tidak ada produk yang ditemukan dengan nama tersebut.
    - **500 Internal Server Error**: Kesalahan server saat mencari produk.
    """
    result = product_services.search_product(
        db,
        product_name
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
        "/all/discount", 
        response_model=product_dtos.AllProductInfoResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Daftar semua produk dengan diskon berhasil diambil",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully retrieved all products with discount",
                            "data": [
                                {
                                    "id": "PROD-20241106001",
                                    "name": "Herbal Supplement",
                                    "description": "A product for daily health...",
                                    "price": 50000,
                                    "discounted_price": 42500,
                                    "highest_promo": 15.0,
                                    "avg_rating": 4.5,
                                    "stock": 100
                                },
                                {
                                    "id": "PROD-20241106002",
                                    "name": "Vitamin C 1000mg",
                                    "description": "Supports immune health...",
                                    "price": 75000,
                                    "discounted_price": 67500,
                                    "highest_promo": 10.0,
                                    "avg_rating": 4.8,
                                    "stock": 200
                                }
                            ]
                        }
                    }
                }
            },
            status.HTTP_204_NO_CONTENT: {
                "description": "Tidak ada produk dengan diskon yang tersedia",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 204,
                            "message": "No products with discount available."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mengambil produk dengan diskon",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mengambil produk dengan diskon."
                        }
                    }
                }
            }
        },
        summary="Get all products with discount"
    )
def read_all_products_with_discount(   
    db: Session = Depends(get_db)
):
    """
    # Ambil Semua Produk yang Mempunyai Diskon #

    Endpoint ini memungkinkan pengguna untuk mengambil semua produk yang sedang memiliki diskon.
    
    **Return:**
    - **200 OK**: Daftar semua produk dengan diskon berhasil diambil.
    - **204 No Content**: Tidak ada produk dengan diskon yang tersedia untuk ditampilkan.
    - **500 Internal Server Error**: Kesalahan server saat mengambil produk dengan diskon.
    
    """
    result = product_services.all_product_with_discount(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/production/{production_id}", 
    response_model=product_dtos.AllProductInfoResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Produk berhasil ditemukan berdasarkan production_id",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Successfully retrieved products for production ID",
                        "data": [
                            {
                                "id": "PROD-20241106001",
                                "name": "Herbal Supplement",
                                "description": "A product for daily health...",
                                "price": 50000,
                                "highest_promo": 15.0,
                                "avg_rating": 4.5,
                                "stock": 100,
                                "production_id": 1
                            },
                            {
                                "id": "PROD-20241106002",
                                "name": "Vitamin C 1000mg",
                                "description": "Supports immune health...",
                                "price": 75000,
                                "highest_promo": 10.0,
                                "avg_rating": 4.8,
                                "stock": 200,
                                "production_id": 1
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produk tidak ditemukan untuk production_id yang diberikan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tidak ada produk yang ditemukan untuk production_id tersebut."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil produk berdasarkan production_id",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat mengambil produk berdasarkan production_id."
                    }
                }
            }
        }
    },
    summary="Get all products by production ID"
)
def read_all_products_by_id_production(
    production_id: int,  # Ambil production_id dari path
    db: Session = Depends(get_db)
):
    """
    # Ambil Semua Produk Berdasarkan production_id #

    Endpoint ini memungkinkan pengguna untuk mengambil semua produk yang terkait dengan ID produksi yang diberikan.
    
    **Parameter:**
    - **production_id** (int): ID produksi yang digunakan untuk mengambil produk.

    **Return:**
    - **200 OK**: Produk berhasil ditemukan berdasarkan production_id.
    - **404 Not Found**: Tidak ada produk yang ditemukan untuk production_id yang diberikan.
    - **500 Internal Server Error**: Kesalahan server saat mengambil produk berdasarkan production_id.
    
    """
    # Langsung kirim production_id ke service tanpa DTO
    result = product_services.all_product_by_id_production(
        db=db,
        production_id=production_id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/loader/production/{production_id}",
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
    limit: int = 9,              # Jumlah data yang akan ditampilkan per halaman
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
        response_model=product_dtos.AllProductInfoResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Produk berhasil ditemukan berdasarkan production_id dan nama produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully retrieved products for production ID and product name",
                            "data": [
                                {
                                    "id": "PROD-20241106001",
                                    "name": "Herbal Supplement",
                                    "description": "A product for daily health...",
                                    "price": 50000,
                                    "highest_promo": 15.0,
                                    "avg_rating": 4.5,
                                    "stock": 100,
                                    "production_id": 1
                                }
                            ]
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Produk tidak ditemukan berdasarkan filter production_id dan nama produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Tidak ada produk yang ditemukan untuk production_id dan nama produk tersebut."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mencari produk berdasarkan filter production_id dan nama produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mencari produk berdasarkan filter production_id dan nama produk."
                        }
                    }
                }
            }
        },
        summary="Search products by production ID and product name"
    )
def search_product_from_filtering_of_id_production(
        production_id: int,
        product_name: str,
        db: Session = Depends(get_db)
):
    """
    # Cari Produk Berdasarkan production_id dan Nama Produk #

    Endpoint ini memungkinkan pengguna untuk mencari produk yang sesuai dengan ID produksi dan nama produk yang diberikan.
    
    **Parameter:**
    - **production_id** (int): ID produksi.
    - **product_name** (str): Nama produk untuk difilter.

    **Return:**
    - **200 OK**: Produk berhasil ditemukan berdasarkan production_id dan nama produk.
    - **404 Not Found**: Tidak ada produk yang cocok dengan filter production_id dan nama produk.
    - **500 Internal Server Error**: Kesalahan server saat mencari produk berdasarkan filter tersebut.
    
    """
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
        response_model=product_dtos.AllProductInfoResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Produk dengan diskon berhasil ditemukan berdasarkan nama produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully retrieved discounted products for the product name",
                            "data": [
                                {
                                    "id": "PROD-20241106001",
                                    "name": "Herbal Supplement",
                                    "description": "A product for daily health...",
                                    "price": 50000,
                                    "highest_promo": 20.0,
                                    "avg_rating": 4.5,
                                    "stock": 50
                                }
                            ]
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Produk tidak ditemukan dengan diskon berdasarkan nama produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Tidak ada produk dengan diskon yang ditemukan untuk nama produk tersebut."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mencari produk dengan diskon berdasarkan nama produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mencari produk dengan diskon berdasarkan nama produk."
                        }
                    }
                }
            }
        },
        summary="Search products with discounts by product name"
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
    response_model=product_dtos.AllProductInfoResponseDto
)
def read_all_products_discount_by_id_production(
    production_id: int,  # Ambil production_id dari path
    db: Session = Depends(get_db)
):
    """
    # Cari Produk dengan Diskon Berdasarkan Nama Produk #

    Endpoint ini memungkinkan pengguna untuk mencari produk yang memiliki diskon berdasarkan nama produk yang diberikan.
    
    **Parameter:**
    - **product_name** (str): Nama produk yang akan dicari diskonnya.

    **Return:**
    - **200 OK**: Produk dengan diskon berhasil ditemukan berdasarkan nama produk.
    - **404 Not Found**: Tidak ada produk dengan diskon yang cocok dengan nama produk yang diberikan.
    - **500 Internal Server Error**: Kesalahan server saat mencari produk dengan diskon berdasarkan nama produk.
    
    """
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
        response_model=product_dtos.ProductDetailResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Detail produk berhasil ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully retrieved product details",
                            "data": {
                                "id": "PROD-20241106001",
                                "name": "Herbal Supplement",
                                "description": "A product for daily health...",
                                "price": 50000,
                                "highest_promo": 15.0,
                                "avg_rating": 4.5,
                                "stock": 100,
                                "production_id": 1,
                                "category": "Health",
                                "created_at": "2024-10-31T10:00:00"
                            }
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Produk dengan ID yang diberikan tidak ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Produk dengan ID yang diberikan tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mengambil detail produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mengambil detail produk."
                        }
                    }
                }
            }
        },
        summary="Get product details by product ID"
    )
def get_product_detail(
    product_id: UUID, 
    db: Session = Depends(get_db)
):
    """
    # Ambil Detail Produk Berdasarkan ID Produk #

    Endpoint ini memungkinkan pengguna untuk mengambil detail produk berdasarkan ID produk yang diberikan.
    
    **Parameter:**
    - **product_id** (UUID): ID produk yang akan diambil detailnya.

    **Return:**
    - **200 OK**: Detail produk berhasil ditemukan berdasarkan ID produk.
    - **404 Not Found**: Produk dengan ID yang diberikan tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan server saat mengambil detail produk.
    
    """
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
    dependencies=[Depends(jwt_service.admin_access_required)],  
    responses={
        status.HTTP_200_OK: {
            "description": "Produk berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Successfully updated product",
                        "data": {
                            "id": "PROD-20241106001",
                            "name": "Herbal Supplement Updated",
                            "description": "Updated description for the product...",
                            "price": 60000,
                            "highest_promo": 25.0,
                            "avg_rating": 4.7,
                            "stock": 150,
                            "production_id": 1,
                            "category": "Health",
                            "created_at": "2024-10-31T10:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Permintaan tidak valid atau data tidak lengkap",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang dikirim tidak lengkap atau tidak valid."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produk dengan ID yang diberikan tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Produk dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Pengguna tidak memiliki hak akses untuk memperbarui produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Anda tidak memiliki hak akses untuk memperbarui produk ini."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui produk."
                    }
                }
            }
        }
    },
    summary="Update product details"
)
def update_product(
    product_id_update: product_dtos.ProductIdToUpdateDTO, 
    product_update: product_dtos.ProductUpdateDTO,
    db: Session = Depends(get_db)
):
    """
    # Perbarui Detail Produk Berdasarkan ID Produk #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk memperbarui detail produk berdasarkan ID produk yang diberikan.
    
    **Parameter:**
    - **product_id_update** (ProductIdToUpdateDTO): ID produk yang akan diperbarui.
    - **product_update** (ProductUpdateDTO): Data produk yang baru untuk diperbarui.

    **Return:**
    - **200 OK**: Produk berhasil diperbarui.
    - **400 Bad Request**: Data yang dikirim tidak valid atau tidak lengkap.
    - **404 Not Found**: Produk dengan ID yang diberikan tidak ditemukan.
    - **403 Forbidden**: Pengguna tidak memiliki hak akses untuk memperbarui produk ini.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui produk.
    
    """
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
        dependencies=[Depends(jwt_service.admin_access_required)],
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Produk berhasil dihapus",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Successfully deleted product",
                            "data": {
                                "id": "PROD-20241106001",
                                "name": "Herbal Supplement",
                                "status": "Deleted"
                            }
                        }
                    }
                }
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Data yang dikirim tidak valid",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 400,
                            "error": "Bad Request",
                            "message": "Data yang dikirim tidak valid atau ID produk tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Produk dengan ID yang diberikan tidak ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Produk dengan ID yang diberikan tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Pengguna tidak memiliki hak akses untuk menghapus produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Anda tidak memiliki hak akses untuk menghapus produk ini."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat menghapus produk",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat menghapus produk."
                        }
                    }
                }
            }
        },
        summary="Delete a product"
    )
def delete_product(
    product_data: product_dtos.DeleteByIdProductDto, 
    db: Session = Depends(get_db)
):
    """
    # Hapus Produk Berdasarkan ID Produk #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk menghapus produk berdasarkan ID produk yang diberikan.
    
    **Parameter:**
    - **product_data** (DeleteByIdProductDto): Data produk yang berisi ID produk yang akan dihapus.

    **Return:**
    - **200 OK**: Produk berhasil dihapus.
    - **400 Bad Request**: Data yang dikirim tidak valid atau ID produk tidak ditemukan.
    - **404 Not Found**: Produk dengan ID yang diberikan tidak ditemukan.
    - **403 Forbidden**: Pengguna tidak memiliki hak akses untuk menghapus produk ini.
    - **500 Internal Server Error**: Kesalahan server saat menghapus produk.
    
    """
    result = product_services.delete_product(
        db, 
        product_data=product_data)
    
    if result.error:
        raise result.error
    
    return result.unwrap()


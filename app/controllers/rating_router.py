from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import rating_dtos
from app.services import rating_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/rating",
    tags=["Rating of Product"]
)

@router.post(
    "/product/{product_id}",
    response_model=rating_dtos.RatingResponseCreateDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Rating produk berhasil dibuat",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Your rate for some product has been created",
                        "data": {
                            "id": 1,
                            "rate": 5,
                            "review": "Produk berkualitas baik",
                            "product_name": "Teh Herbal",
                            "rater_name": "User123",
                            "created_at": "2024-10-31T10:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Token tidak valid atau pengguna tidak terautentikasi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Not Authenticated."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produk atau pengguna tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Produk dengan ID ini tidak ditemukan atau pengguna tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Terjadi konflik saat mengakses data",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Konflik saat menyimpan rating produk."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat menyimpan rating produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat menyimpan rating produk."
                    }
                }
            }
        }
    },
    summary="Create a rating for a specific product"
)
def give_a_rate_of_product(
    product_id: UUID,
    create_rate: rating_dtos.RatingCreateDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    """
    # Berikan Rating pada Produk #

    Endpoint ini memungkinkan pengguna untuk memberikan rating pada produk tertentu.
    
    **Parameter:**
    - **product_id** (UUID): ID dari produk yang ingin diberi rating.
    - **create_rate** (RatingCreateDto): Rating dan ulasan dari pengguna.
    - **jwt_token**: Token JWT yang berisi ID pengguna.

    **Return:**
    - **201 Created**: Rating produk berhasil dibuat.
    - **404 Not Found**: Produk atau pengguna tidak ditemukan.
    - **409 Conflict**: Terjadi konflik saat mengakses data.
    - **500 Internal Server Error**: Kesalahan server saat menyimpan rating produk.
    """
    result = rating_services.create_rating(
        db,
        product_id,
        create_rate,
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/my-rating-products-list",
    response_model=List[rating_dtos.MyRatingListDto],
    responses={
        status.HTTP_200_OK: {
            "description": "Daftar rating produk pengguna berhasil diambil",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "rate": 5,
                            "review": "Produk sangat bagus",
                            "product_name": "Teh Herbal",
                            "created_at": "2024-10-31T10:00:00"
                        }
                    ]
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Token tidak valid atau pengguna tidak terautentikasi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Not Authenticated."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Pengguna tidak ditemukan atau tidak memiliki rating produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Daftar rating produk dari pengguna ini tidak ditemukan."
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Terjadi konflik saat mengakses data",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Terjadi konflik saat mengambil data rating produk pengguna."
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan di server",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan di server saat mengambil data rating produk."
                    }
                }
            }
        }
    },
    summary="Get user's product rating list"
)
async def get_my_list_products(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Ambil Daftar Rating Produk Pengguna #

    Endpoint ini digunakan untuk mengambil daftar rating produk yang diberikan oleh pengguna berdasarkan ID yang terdapat dalam token JWT.

    **Return:**

    - **200 OK**: Daftar rating produk pengguna berhasil diambil.
    - **404 Not Found**: Pengguna tidak ditemukan atau tidak memiliki rating produk.
    - **409 Conflict**: Terjadi konflik saat mengakses data.
    - **500 Internal Server Error**: Terjadi kesalahan di server.
    """
    result = rating_services.my_rating_list(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()

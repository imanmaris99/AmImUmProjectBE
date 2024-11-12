from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from app.dtos import category_dtos
from app.models.tag_category_model import TagCategoryModel

from app.services import category_services
from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/categories",
    tags=["Tag-Categories"]
)

@router.post(
    "/post", 
    response_model=category_dtos.CategoryCreateResponseDto,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(jwt_service.admin_access_required)],
    responses={
        status.HTTP_201_CREATED: {
            "description": "Kategori berhasil dibuat",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Category successfully created",
                        "data": {
                            "id": 1,
                            "name": "Jamu Produksi Pabrik",
                            "description": "menggunakan teknologi yang modern sehingga dapat diproduksi dalam jumlah yang besar dengan kualitas yang baik.",
                            "created_at": "2024-11-09T10:00:00",
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Data yang diberikan tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data kategori tidak valid, pastikan semua field sudah terisi dengan benar."
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
            "description": "Kesalahan server saat membuat kategori",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat membuat kategori."
                    }
                }
            }
        }
    },
    summary="Create a new category"
)
def create_categories(
    category_create_dto: category_dtos.CategoryCreateDto, 
    db: Session = Depends(get_db),
):
    """
    # Buat Kategori Baru #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk membuat kategori baru.
    
    **Parameter:**
    - **category_create_dto** (CategoryCreateDto): Data kategori baru yang akan dibuat.

    **Return:**
    - **201 Created**: Kategori berhasil dibuat.
    - **400 Bad Request**: Data kategori yang diberikan tidak valid.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **500 Internal Server Error**: Kesalahan server saat membuat kategori.
    
    """
    result = category_services.create_categories(
        db, 
        category_create_dto
    )
    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/all", 
    response_model=category_dtos.AllCategoryInfoResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Daftar kategori berhasil diambil",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Data berhasil diambil",
                        "data": [
                            {
                                "id": 1,
                                "name": "Jamu Produksi Pabrik",
                                "description": "menggunakan teknologi yang modern sehingga dapat diproduksi dalam jumlah yang besar dengan kualitas yang baik.",
                                "created_at": "2024-11-09T10:00:00"
                            },
                            {
                                "id": 2,
                                "name": "Jamu Produksi Rumahan",
                                "description": "menggunakan bahan alami langsung dari petani yang dapat diproduksi langsung dalam jumlah terbatas dengan kualitas yang baik.",
                                "created_at": "2024-11-09T11:00:00"
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil kategori",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat mengambil daftar kategori."
                    }
                }
            }
        }
    },
    summary="Get all categories"
)
def read_categories(
    # jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],    
    db: Session = Depends(get_db)
):
    """
    # Ambil Semua Kategori #

    Endpoint ini memungkinkan untuk mengambil semua kategori yang terdaftar di database.
    
    **Return:**
    - **200 OK**: Daftar kategori berhasil diambil.
    - **500 Internal Server Error**: Kesalahan server saat mengambil kategori.
    
    """
    result = category_services.get_all_categories(db)

    if result.error:
        raise result.error

    return result.unwrap()
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
    rate:rating_dtos.RatingCreateOfIdProductDto,
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
        rate,
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

@router.put(
        "/edit/{rating_id}", 
        response_model=rating_dtos.ReviewInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Review berhasil diperbarui",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Updated Info about Review and rating from this product ID {rating_id} has been successful",
                            "data": {
                                "rate": 4,
                                "review": "Produk cukup baik, namun perlu perbaikan"
                            }
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Pengguna tidak memiliki hak akses",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Pengguna tidak diizinkan untuk memperbarui review ini."
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Review tidak ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Review dan rating untuk ID produk ini tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_409_CONFLICT: {
                "description": "Konflik saat mengupdate review",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Konflik terjadi saat memperbarui review."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat memperbarui review",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat memperbarui review."
                        }
                    }
                }
            }
        },
        summary="Update an existing review for a product"
    )
def update_my_product_review(
        review_id_update: rating_dtos.ReviewIdToUpdateDto,
        review_update: rating_dtos.ReviewDataUpdateDTO,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Perbarui Review Produk #

    Endpoint ini digunakan untuk memperbarui review dan rating untuk produk tertentu yang dimiliki pengguna.

    **Parameter:**
    - **rating_id** (int): ID dari review yang ingin diperbarui.
    - **review_update** (ReviewDataUpdateDTO): Data review dan rating baru dari pengguna.
    - **jwt_token**: Token JWT yang berisi ID pengguna yang sudah terautentikasi.

    **Return:**
    - **200 OK**: Review berhasil diperbarui.
    - **403 Forbidden**: Pengguna tidak memiliki hak akses untuk memperbarui review ini.
    - **404 Not Found**: Review tidak ditemukan.
    - **409 Conflict**: Konflik terjadi saat mengupdate data.
    - **500 Internal Server Error**: Kesalahan tak terduga di server.
    """
    result = rating_services.edit_my_review(
        db, 
        review_id_update=review_id_update, 
        review_update=review_update, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.data

@router.delete(
        "/delete/{rating_id}",
        response_model=rating_dtos.DeleteReviewResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Review berhasil dihapus",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Your review has been deleted",
                            "data": {
                                "rating_id": 1,
                                "rate": 5,
                                "review": "Produk bagus sekali!",
                                "product_name": "Teh Herbal"
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
                            "message": "Token tidak valid atau pengguna tidak memiliki akses."
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Review tidak ditemukan atau tidak dimiliki oleh pengguna",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Review dengan ID ini tidak ditemukan atau tidak dimiliki oleh pengguna."
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
                            "message": "Konflik saat menghapus review."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat menghapus review",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat menghapus review."
                        }
                    }
                }
            }
        },
        summary="Delete a product review"
    )
def delete_my_product_review(
        review_id_delete: rating_dtos.DeleteReviewDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Hapus Review Produk #

    Endpoint ini memungkinkan pengguna untuk menghapus review produk tertentu yang sudah dibuat.

    **Parameter:**
    - **rating_id** (int): ID dari review yang ingin dihapus.
    - **jwt_token**: Token JWT yang berisi ID pengguna.

    **Return:**
    - **200 OK**: Review berhasil dihapus.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak terautentikasi.
    - **404 Not Found**: Review tidak ditemukan atau tidak dimiliki oleh pengguna.
    - **409 Conflict**: Terjadi konflik saat menghapus data.
    - **500 Internal Server Error**: Kesalahan server saat menghapus review.
    """
    result = rating_services.delete_my_review(
        db, 
        review_id_delete=review_id_delete, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()
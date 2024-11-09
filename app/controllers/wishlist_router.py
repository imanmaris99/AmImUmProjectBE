from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import wishlist_dtos
from app.services import wishlist_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/wishlist",
    tags=["Product Wishlist"]
)

@router.post(
    "/product/{product_id}",
    response_model=wishlist_dtos.WishlistResponseCreateDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Wishlist item successfully added",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Your wishlist for the product has been saved",
                        "data": {
                            "id": 0,
                            "product_name": "string",
                            "created_at": "2024-11-03T06:19:31.069Z"
                        }
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission to add to wishlist",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "User is not authorized to add to the wishlist."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Product not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "The specified product was not found."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflict when adding to wishlist",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Product is already in the wishlist."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while adding to the wishlist."
                    }
                }
            }
        }
    },
    summary="Add Product to Wishlist"
)
def post_my_wishlist(
    # product_id: UUID,
    wish:wishlist_dtos.WishlistCreateOfIdProductDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    """
    # Add Product to Wishlist #

    Endpoint ini menambahkan produk yang ditentukan ke dalam wishlist pengguna.

    **Parameter:**
    - **product_id** (UUID): ID produk yang ingin ditambahkan ke wishlist.
    - **jwt_token** (TokenPayLoad): Token payload untuk verifikasi user.

    **Return:**
    - **201 Created**: Wishlist berhasil ditambahkan.
    - **403 Forbidden**: Pengguna tidak diizinkan menambah ke wishlist.
    - **404 Not Found**: Produk tidak ditemukan.
    - **409 Conflict**: Produk sudah ada dalam wishlist.
    - **500 Internal Server Error**: Kesalahan tak terduga saat menambahkan ke wishlist.
    
    """
    result = wishlist_services.post_wishlist(
        db,
        wish,
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()

@router.get(
    "/total-items",
    response_model=wishlist_dtos.AllItemNotificationDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "User's wishlist retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Your all of products wishlist success calculated",
                        "total_items": 1,
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User not authorized to view wishlist",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "You do not have permission to view this wishlist."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Wishlist of Product not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "The Wishlist of product was not found."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected server error",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while retrieving the wishlist."
                    }
                }
            }
        }
    },
    summary="Get User's Total Wishlist Products"
)
async def get_total_wishlist(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):    
    """
    # Get User's Total Wishlist Products #

    Endpoint ini mengembalikan kalkulasi total semua daftar produk dalam wishlist pengguna.

    **Parameter:**
    - **jwt_token** (TokenPayLoad): Token payload yang memberikan akses ke data pengguna.
    - **db** (Session): Koneksi database untuk mendapatkan data.

    **Return:**
    - **200 OK**: Berhasil mendapatkan kalkulasi total semua produk dalam wishlist pengguna.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk mengakses wishlist ini.
    - **404 Not Found**: Produk Wishlist tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan tak terduga saat mengambil wishlist.
    
    """
    result = wishlist_services.total_items(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/my-products-wishlist",
    response_model=wishlist_dtos.AllWishlistResponseCreateDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "User's wishlist retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Your all of products wishlist success to access",
                        "total_records": 1,
                        "data": [
                            {
                                "id": 0,
                                "product_name": "string",
                                "product_variant": [
                                    {
                                    "id": 0,
                                    "variant": "string",
                                    "img": "string",
                                    "discount": 0,
                                    "discounted_price": 0,
                                    "updated_at": "2024-10-21T13:01:38.381228Z"
                                    }
                                ],
                                "created_at": "2024-11-03T06:19:31.047Z"
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User not authorized to view wishlist",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "You do not have permission to view this wishlist."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Wishlist of Product not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "The Wishlist of product was not found."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected server error",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while retrieving the wishlist."
                    }
                }
            }
        }
    },
    summary="Get User's Wishlist Products"
)
async def get_my_products_wishlist(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Get User's Wishlist Products #

    Endpoint ini mengembalikan daftar produk dalam wishlist pengguna.

    **Parameter:**
    - **jwt_token** (TokenPayLoad): Token payload yang memberikan akses ke data pengguna.
    - **db** (Session): Koneksi database untuk mendapatkan data.

    **Return:**
    - **200 OK**: Berhasil mendapatkan semua produk dalam wishlist pengguna.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk mengakses wishlist ini.
    - **404 Not Found**: Produk Wishlist tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan tak terduga saat mengambil wishlist.
    
    """
    result = wishlist_services.my_wishlist(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.delete(
    "/delete/{wishlist_id}",
    response_model=wishlist_dtos.DeleteWishlistResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Wishlist item deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Your product wishlist with ID 1 has been deleted",
                        "data": {
                            "wishlist_id": 1,
                            "product_name": "Buyung Upik"
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Wishlist item not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Wishlist item with the specified ID does not exist."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User not authorized to delete this wishlist item",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "You do not have permission to delete this wishlist item."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Unexpected server error",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while deleting the wishlist item."
                    }
                }
            }
        }
    },
    summary="Delete Product from Wishlist"
)
def delete_my_product_wishlist(
        wishlist_data: wishlist_dtos.DeleteByIdWishlistDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Delete Product from Wishlist #

    Endpoint ini digunakan untuk menghapus produk tertentu dari wishlist pengguna.

    **Parameter:**
    - **wishlist_data** (DeleteByIdWishlistDto): Data ID wishlist yang akan dihapus.
    - **jwt_token** (TokenPayLoad): Token payload yang memberikan akses ke data pengguna.
    - **db** (Session): Koneksi database untuk menghapus data wishlist.

    **Return:**
    - **200 OK**: Berhasil menghapus item wishlist.
    - **404 Not Found**: Item wishlist tidak ditemukan.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk menghapus item wishlist ini.
    - **500 Internal Server Error**: Kesalahan tak terduga saat menghapus item wishlist.
    
    """
    result = wishlist_services.delete_wishlist(
        db, 
        wishlist_data, 
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()

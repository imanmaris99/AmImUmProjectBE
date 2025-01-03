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
    responses={
        status.HTTP_201_CREATED: {
            "description": "Item berhasil ditambahkan ke keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Item berhasil ditambahkan ke keranjang",
                        "data": {
                            "product_id": "123e4567-e89b-12d3-a456-426614174000",
                            "variant_id": "abc123variant",
                            "quantity": 1,
                            "added_at": "2024-11-09T12:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request tidak valid, misalnya data tidak lengkap atau tidak ditemukan",
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
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission to add to wishlist",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "User is not authorized."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produk atau varian tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Produk atau varian dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat menambahkan item ke keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan saat menambahkan item ke keranjang."
                    }
                }
            }
        }
    },
    summary="Post product to Cart"
)
def post_my_item_of_cart(
    cart: cart_dtos.CartCreateOfIdProductDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    """
    # Tambah Item ke Keranjang #
    
    Endpoint ini memungkinkan pengguna untuk menambahkan item ke dalam keranjang belanja dengan 
    memberikan ID produk dan varian yang diinginkan.
    
    **Parameter:**
    - **cart** (CartCreateOfIdProductDto): Data item yang akan ditambahkan ke keranjang, termasuk ID produk dan varian.
    - **jwt_token**: Token JWT yang digunakan untuk mengidentifikasi pengguna yang sedang login.
    
    **Return:**
    - **201 Created**: Item berhasil ditambahkan ke keranjang.
    - **400 Bad Request**: Permintaan tidak valid.
    - **403 Forbidden**: Pengguna tidak diizinkan menambah ke cart.
    - **404 Not Found**: Produk atau varian yang diminta tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan server saat menambahkan item ke keranjang.
    
    """
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
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request tidak valid, misalnya tidak ada produk di keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Tidak ada produk di keranjang."
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
                        "message": "User is not authorized."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Pengguna tidak ditemukan, kemungkinan token tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Pengguna tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil data keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan saat mengambil data keranjang."
                    }
                }
            }
        }
    },
    summary="Get all list product in my Cart"
)
async def get_my_cart(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Ambil Keranjang Belanja Pengguna #

    Endpoint ini memungkinkan pengguna untuk mengambil data keranjang belanja mereka berdasarkan token JWT yang diberikan.
    
    **Parameter:**
    - **jwt_token**: Token JWT yang digunakan untuk mengidentifikasi pengguna yang sedang login.

    **Return:**
    - **200 OK**: Data keranjang belanja berhasil diambil.
    - **400 Bad Request**: Tidak ada produk di keranjang atau request tidak valid.
    - **403 Forbidden**: Pengguna tidak memiliki akses get cart.
    - **404 Not Found**: Pengguna tidak ditemukan atau token tidak valid.
    - **500 Internal Server Error**: Terjadi kesalahan server saat mengambil data keranjang.
    
    """
    result = cart_services.my_cart(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
    "/total-items",
    response_model=cart_dtos.AllItemNotificationDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "User not authorized to view cart",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "You do not have permission to view this cart."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "List Product Item of Cart not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "The product item of cart was not found."
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
                        "message": "An unexpected error occurred while retrieving the cart."
                    }
                }
            }
        }
    },
    summary="Get User's Total Item Products in Cart"
)
async def get_total_item_in_my_cart(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Get User's Total Item Products in Cart #

    Endpoint ini mengembalikan kalkulasi total semua daftar produk dalam cart pengguna.

    **Parameter:**
    - **jwt_token** (TokenPayLoad): Token payload yang memberikan akses ke data pengguna.
    - **db** (Session): Koneksi database untuk mendapatkan data.

    **Return:**
    - **200 OK**: Berhasil mendapatkan kalkulasi total semua produk dalam cart pengguna.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk mengakses cart ini.
    - **404 Not Found**: Produk cart tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan tak terduga saat mengambil cart.
    
    """
    result = cart_services.total_items(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.put(
        "/update-quantity/{cart_id}", 
        response_model=cart_dtos.CartInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Permintaan tidak valid, seperti jumlah negatif atau produk tidak ada",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Jumlah yang dimasukkan tidak valid atau produk tidak ditemukan dalam keranjang."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Token tidak valid atau pengguna tidak diizinkan memperbarui item ini",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Anda tidak memiliki izin untuk memperbarui item keranjang ini."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Item dalam keranjang dengan ID yang diberikan tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Item keranjang dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui item keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui jumlah item dalam keranjang."
                    }
                }
            }
        }
    },
    summary="Update cart item quantity"
)
def update_my_quantity_item(
        cart: cart_dtos.UpdateByIdCartDto,
        quantity_update: cart_dtos.UpdateQuantityItemDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Perbarui Jumlah Item di Keranjang #

    Endpoint ini memungkinkan pengguna memperbarui jumlah item dalam keranjang mereka berdasarkan ID keranjang.

    **Parameter:**
    - **cart** (UpdateByIdCartDto): Data keranjang, berisi ID keranjang.
    - **quantity_update** (UpdateQuantityItemDto): Data pembaruan jumlah.
    - **jwt_token** (TokenPayLoad): Token pengguna untuk memastikan bahwa pengguna memiliki hak akses.
    - **db** (Session): Objek sesi database.

    **Return:**
    - **200 OK**: Jumlah item dalam keranjang berhasil diperbarui.
    - **400 Bad Request**: Data tidak valid atau jumlah negatif.
    - **403 Forbidden**: Pengguna tidak memiliki izin untuk memperbarui item.
    - **404 Not Found**: Item dalam keranjang dengan ID yang diberikan tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui item keranjang.
    
    """
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
    "/update-activate/{cart_id}", 
    response_model=cart_dtos.CartInfoUpdateResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Item produk yang akan diaktivasi tidak ada dalam keranjang."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "User is not authorized."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Keranjang tidak ditemukan atau produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Keranjang atau produk tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan saat melakukan aktivasi item",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan saat pembaruan item di kranjang."
                    }
                }
            }
        }
    },
    summary="Update activate status of item product in my Cart"
)
def update_my_activate_item(
        cart: cart_dtos.UpdateByIdCartDto,
        activate_update: cart_dtos.UpdateActivateItemDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Aktivasi Status Item Produk dalam Keranjang #

    Endpoint ini memungkinkan pengguna untuk memperbarui status aktivasi item yang ada di keranjang.

    **Parameter:**
    - **cart_id**: ID keranjang produk yang ingin diperbarui.
    - **activate_update**: status aktifasi yang ingin diperbarui di keranjang.

    **Return:**
    - **200 OK**: Jumlah produk berhasil diperbarui.
    - **400 Bad Request**: Jumlah produk tidak valid atau request tidak lengkap.
    - **403 Forbidden**: Pengguna tidak memiliki akses untuk memperbarui cart.
    - **404 Not Found**: Item Produk di keranjang tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan saat memperbarui data.
    
    """
    result = cart_services.update_activate_item(
        db, 
        cart=cart, 
        activate_update=activate_update, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.data

@router.put(
    "/update-activate-all", 
    response_model=cart_dtos.CartInfoUpdateAllActivateResponseDto,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Item produk yang akan diaktivasi tidak ada dalam keranjang."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "User does not have permission",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "User is not authorized."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Keranjang tidak ditemukan atau produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Keranjang atau produk tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan saat melakukan aktivasi item",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan saat pembaruan item di kranjang."
                    }
                }
            }
        }
    },    
    summary="Update activate status of all item product in my Cart"
)
async def update_all_cart_items(
    activate_update: cart_dtos.UpdateActivateItemDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)

):
    """
    # Memperbarui Semua Status Aktif Item Produk dalam Keranjang #

    Endpoint ini memungkinkan pengguna untuk memperbarui atau update semua cart milik user yang sedang login..

    **Parameter:**
    - **activate_update**: status aktifasi yang ingin diperbarui di keranjang.

    **Return:**
    - **200 OK**: Berhasil melakukan pembaruan status aktif item produk di keranjang.
    - **400 Bad Request**: Jumlah produk tidak valid atau request tidak lengkap.
    - **403 Forbidden**: Pengguna tidak memiliki akses untuk memperbarui cart.
    - **404 Not Found**: Item Produk di keranjang tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan saat memperbarui data.
    
    """
    
    result = cart_services.update_activate_all_items(
        db, 
        activate_update, 
        user_id=jwt_token.id)
    
    if result.error:
        raise result.error

    return result.data

@router.delete(
    "/delete/{cart_id}",
    response_model=cart_dtos.DeleteCartResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Item berhasil dihapus dari keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Item berhasil dihapus dari keranjang",
                        "data": {
                            "cart_id": "12345abcd",
                            "product_id": "123e4567-e89b-12d3-a456-426614174000",
                            "variant_id": "abc123variant",
                            "quantity": 1,
                            "deleted_at": "2024-11-09T12:45:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request tidak valid, mungkin ID tidak ditemukan atau produk tidak ada di keranjang",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "ID keranjang atau produk tidak ditemukan atau tidak valid."
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
                        "message": "User is not authorized."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Keranjang atau item tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Item dalam keranjang tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan pada server saat menghapus item",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan pada server saat menghapus item dari keranjang."
                    }
                }
            }
        }
    },
    summary="Delete product item in my Cart"
)
def delete_my_item_cart(
        cart: cart_dtos.DeleteByIdCartDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Menghapus Item dari Keranjang Belanja #

    Endpoint ini memungkinkan pengguna untuk menghapus item dari keranjang belanja mereka.

    **Parameter:**
    - **cart_id**: ID keranjang produk yang ingin dihapus.

    **Return:**
    - **200 OK**: Item berhasil dihapus.
    - **400 Bad Request**: Request tidak valid, mungkin ID tidak ditemukan atau produk tidak ada di keranjang.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk akses delete item di cart.
    - **404 Not Found**: Keranjang atau item tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan saat menghapus item dari keranjang.
    
    """
    result = cart_services.delete_item(
        db, 
        cart=cart, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()
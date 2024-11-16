from fastapi import APIRouter, Depends, status

from typing import List, Annotated, Optional

from sqlalchemy.orm import Session

from app.dtos import shipment_address_dtos
from app.services import shipment_address_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/shipment-address",
    tags=["Address Shipping"]
)

@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    response_model=shipment_address_dtos.ShipmentAddressResponseDto,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Alamat pengiriman berhasil disimpan.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Alamat pengiriman berhasil dibuat.",
                        "data": {
                            "id": 1,
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "address": "Jl. Mawar No.10",
                            "city": "Jakarta",
                            "postal_code": "12345",
                            "country": "Indonesia",
                            "created_at": "2024-11-16T12:00:00",
                            "updated_at": "2024-11-16T12:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Data permintaan tidak valid.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Permintaan Tidak Valid",
                        "message": "Data yang dikirimkan tidak sesuai dengan format yang diharapkan."
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Akses tidak diizinkan.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 401,
                        "error": "Tidak Diizinkan",
                        "message": "Token autentikasi tidak valid atau tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan pada server.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Kesalahan Server",
                        "message": "Terjadi kesalahan tak terduga saat memproses permintaan."
                    }
                }
            }
        },
    },
    summary="Post Info Address Shipping to Database"
)
def save_shipping_address(
    request_data: shipment_address_dtos.ShipmentAddressCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    ### Menyimpan Alamat Pengiriman Baru

    Endpoint ini digunakan untuk menyimpan alamat pengiriman ke dalam database.  
    Hanya pengguna yang sudah masuk (authenticated) yang dapat mengakses endpoint ini.

    **Parameter:**
    - **request_data**: Data alamat pengiriman yang ingin disimpan.
    - **jwt_token**: Informasi pengguna yang diperoleh dari JWT.
    - **db**: Sesi database.

    **Returns:**
    - **201 Created**: Alamat pengiriman berhasil disimpan.
    - **400 Bad Request**: Data yang dikirimkan tidak valid.
    - **401 Unauthorized**: Pengguna tidak memiliki izin akses.
    - **500 Internal Server Error**: Kesalahan tak terduga di server.
    """
    result = shipment_address_services.create_shipment_address(
        request_data, 
        jwt_token.id,
        db
    )
    
    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
    "/my-address",
    response_model=shipment_address_dtos.AllAddressListResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Daftar alamat pengiriman yang terhubung dengan pengguna.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "data": [
                            {
                                "address_id": 1,
                                "recipient_name": "John Doe",
                                "address_line": "123 Jalan Utama",
                                "city": "Jakarta",
                                "province": "DKI Jakarta",
                                "postal_code": "12345",
                                "phone_number": "+62 812 3456 7890",
                                "is_default": True
                            },
                            {
                                "address_id": 2,
                                "recipient_name": "Jane Doe",
                                "address_line": "456 Jalan Samping",
                                "city": "Bandung",
                                "province": "Jawa Barat",
                                "postal_code": "67890",
                                "phone_number": "+62 813 9876 5432",
                                "is_default": False
                            }
                        ]
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Pengguna tidak memiliki otorisasi untuk mengakses resource ini.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 401,
                        "error": "Unauthorized",
                        "message": "Pengguna harus login untuk mengakses alamat pengiriman."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan pada server.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan tak terduga saat mengambil data alamat."
                    }
                }
            }
        }
    },
    summary="Get all data shipping address in my account"
)
async def get_my_shipping_address(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    ### Ambil Semua Alamat Pengiriman
    Endpoint ini digunakan untuk mengambil semua alamat pengiriman yang terhubung dengan akun pengguna.

    **Parameter:**
    - **jwt_token**: Diambil dari header otorisasi pengguna.
    - **db**: Dependency session database.

    **Respon:**
    - **200 OK**: Mengembalikan daftar alamat pengiriman.
    - **401 Unauthorized**: Jika pengguna tidak memiliki otorisasi (belum login).
    - **500 Internal Server Error**: Jika terjadi kesalahan tak terduga.
    """
    result = shipment_address_services.my_shipping_address(
        db, 
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.put(
    "/edit/{address_id}", 
    response_model=shipment_address_dtos.ShipmentAddressResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Alamat tujuan pengiriman berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Alamat tujuan pengiriman berhasil diperbaharui.",
                        "data": {
                            "id": 1,
                            "user_id": "123e4567-e89b-12d3-a456-426614174000",
                            "address": "Jl. Mawar No.10",
                            "city": "Jakarta",
                            "postal_code": "12345",
                            "country": "Indonesia",
                            "created_at": "2024-11-16T12:00:00",
                            "updated_at": "2024-11-16T12:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Data yang diberikan tidak valid atau format tidak sesuai",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang diberikan tidak valid atau format tidak sesuai."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Alamat tidak ditemukan berdasarkan ID yang diberikan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Alamat dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui data berat pengiriman",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui data berat pengiriman."
                    }
                }
            }
        }
    },
    summary="Update Data of Shipment Address Destination"
)
def update_my_address(
        update_request: shipment_address_dtos.ShipmentAddressIdToUpdateDto,
        address_data: shipment_address_dtos.ShipmentAddressCreateDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Update Alamat Tujuan Pengiriman #

    Endpoint ini memungkinkan pengguna dengan akses user yang sudah login dapat untuk memperbarui informasi tujuan pengiriman berdasarkan ID alamat yang sudah disimpan sebelumnya.

    **Parameter:**
    - **update_request** (CourierIdToUpdateDto): Data ID kurir yang akan diperbarui.
    - **address_data** (CourierDataWeightUpdateDTO): Data baru untuk berat pengiriman.
    - **jwt_token** (TokenPayLoad): Payload token JWT yang digunakan untuk memverifikasi akses pengguna.
    
    **Return:**
    - **200 OK**: Alamat tujuan pengiriman berhasil diperbarui.
    - **400 Bad Request**: Data yang diberikan tidak valid atau format tidak sesuai.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini.
    - **404 Not Found**: Alamat tidak ditemukan berdasarkan ID yang diberikan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui data alamat tujuan pengiriman.
    """
    result = shipment_address_services.update_shipment_address(
        db, 
        update_request, 
        address_data, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.delete(
    "/delete/{adrress_id}",
    response_model=shipment_address_dtos.DeleteAddressResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Shipment address item deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Your data of shipment address with ID 1 has been deleted",
                        "data": {
                            "address_id": 1,
                            "name": "Buyung",
                            "phone": "+6287767546384",
                            "address": "Jln. Wangi semerbak, another place in this island"
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Address item not found",
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
            "description": "User not authorized to delete this address item",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "You do not have permission to delete this address item."
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
    summary="Delete Data of Shipment Address"
)
def delete_my_shipping_address(
        request_delete: shipment_address_dtos.DeleteAddressDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Delete Data Alamat Tujuan Pengiriman #

    Endpoint ini digunakan untuk menghapus produk tertentu dari wishlist pengguna.

    **Parameter:**
    - **request_delete** (DeleteAddresstDto): Data ID address yang akan dihapus.
    - **jwt_token** (TokenPayLoad): Token payload yang memberikan akses ke data pengguna.
    - **db** (Session): Koneksi database untuk menghapus data address.

    **Return:**
    - **200 OK**: Berhasil menghapus item address.
    - **404 Not Found**: Item address tidak ditemukan.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk menghapus item address ini.
    - **500 Internal Server Error**: Kesalahan tak terduga saat menghapus item address.
    
    """
    result = shipment_address_services.delete_address(
        db, 
        request_delete, 
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/owner-address",
    response_model=shipment_address_dtos.ShipmentAddressResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Alamat pemilik toko berhasil diambil.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Alamat berhasil ditemukan.",
                        "data": {
                            "id": "9d899cc1-ec4e-4f54-9e3d-89502657db91",
                            "street": "Jl. Merdeka No. 123",
                            "city": "Jakarta",
                            "province": "DKI Jakarta",
                            "postal_code": "10110",
                            "country": "Indonesia",
                            "updated_at": "2024-11-15T10:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Alamat tidak ditemukan.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Alamat pemilik toko tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Akses tidak diizinkan.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Pengguna tidak diizinkan untuk mengakses informasi ini."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan pada server.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan tak terduga saat mengambil data alamat."
                    }
                }
            }
        }
    },
    summary="Get shipping address of the store owner (accessible by all users)"
)
async def get_store_owner_address(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    ### Ambil Alamat Asal Toko Pengirim

    Endpoint ini secara otomatis menampilkan alamat dari pemilik toko dengan ID tertentu,
    tanpa memerlukan input ID pemilik toko dalam URL. Semua user yang login dapat mengakses
    alamat ini.

    **Parameter:**
    - **jwt_token**: Diambil dari header otorisasi pengguna.
    - **db**: Dependency session database.

    **Respon:**
    - **200 OK**: Mengembalikan daftar alamat pengiriman.
    - **401 Unauthorized**: Jika pengguna tidak memiliki otorisasi (belum login).
    - **403 Forbidden**: Akses tidak diijinkan.
    - **500 Internal Server Error**: Jika terjadi kesalahan tak terduga.

    """
    result = shipment_address_services.accessible_address(
        db=db,
        user_id=jwt_token.id,  # ID user yang sedang melakukan request (dari JWT)
        target_user_id="9d899cc1-ec4e-4f54-9e3d-89502657db91"  # Hardcode ID pemilik toko
    )

    if result.error:
        raise result.error
    
    return result.unwrap()
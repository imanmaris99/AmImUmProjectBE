from fastapi import APIRouter, Depends, status
from typing import Annotated
from sqlalchemy.orm import Session

from app.dtos import shipment_dtos
from app.services.shipment_services import new_post, create_shipment, my_shipping, update_shipping, update_activate, delete_shipment
from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service


router = APIRouter(
    prefix="/shipment",
    tags=["Shipment Information"]
)

@router.post(
    "/create-shipment",
    response_model=shipment_dtos.ShipmentResponseDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Shipment berhasil dibuat",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Shipment has been successfully created",
                        "data": {
                            "shipment_id": "string",  # Contoh ID shipment yang dihasilkan
                            "courier_id": 0,  # Contoh ID kurir
                            "address_id": 0,  # Contoh ID alamat
                            "code_tracking": "string",  # Contoh kode pelacakan
                            "created_at": "2024-11-16T01:36:46.310Z"  # Waktu pembuatan
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request data tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang diberikan tidak valid. Pastikan semua informasi lengkap dan benar."
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Token tidak valid atau pengguna tidak terautentikasi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 401,
                        "error": "Unauthorized",
                        "message": "Token tidak valid atau pengguna tidak terautentikasi."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat membuat shipment",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan tak terduga saat mencoba membuat shipment."
                    }
                }
            }
        }
    },
    summary="Create a new shipment"
)
def create_shipment_route(
    request_data: shipment_dtos.ShipmentCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    """
    # Membuat Shipment Baru #

    Endpoint ini digunakan untuk membuat shipment baru berdasarkan data yang diberikan oleh pengguna.

    **Parameter:**
    - **request_data** (ShipmentCreateDto): Data untuk membuat shipment baru.
    - **jwt_token** (TokenPayLoad): Token pengguna yang digunakan untuk autentikasi.
    
    **Return:**
    - **201 Created**: Shipment berhasil dibuat dan ID shipment serta detail lainnya dikembalikan.
    - **400 Bad Request**: Jika data yang dikirim tidak valid atau ada kesalahan lainnya.
    - **401 Unauthorized**: Jika token tidak valid atau pengguna tidak terautentikasi.
    - **500 Internal Server Error**: Jika terjadi kesalahan pada server saat memproses permintaan.
    """
    # Panggil fungsi service untuk membuat shipment
    result = create_shipment(
        request_data=request_data, 
        user_id=jwt_token.id, 
        db=db
    )

    if result.error:
        raise result.error

    return result.unwrap()

@router.post(
    "/new-shipment",
    response_model=shipment_dtos.ShipmentResponseDto,
    status_code=status.HTTP_201_CREATED,
    summary="Post a new shipment"
)
def create_new_shipment(
    request_data: shipment_dtos.RequestIdToUpdateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    result = new_post(
        request_data=request_data, 
        user_id=jwt_token.id, 
        db=db
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/my-list",
    response_model=shipment_dtos.MyListShipmentResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
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
    summary="Get all data shipping in my account"
)
async def get_my_shipping(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    ### Ambil Semua Daftar Tujuan Pengiriman dan Biayanya
    Endpoint ini digunakan untuk mengambil semua alamat pengiriman, courier beserta biaya yang terhubung dengan akun pengguna.

    **Parameter:**
    - **jwt_token**: Diambil dari header otorisasi pengguna.
    - **db**: Dependency session database.

    **Respon:**
    - **200 OK**: Mengembalikan daftar info pengiriman.
    - **401 Unauthorized**: Jika pengguna tidak memiliki otorisasi (belum login).
    - **500 Internal Server Error**: Jika terjadi kesalahan tak terduga.
    """
    result = my_shipping(
        db, 
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


# @router.put(
#     "/edit/{shipment_id}/{address_id}/{courier_id}", 
#     response_model=shipment_dtos.MyShipmentUpdateResponseDto,
#     status_code=status.HTTP_200_OK,
#     responses={
#         status.HTTP_400_BAD_REQUEST: {
#             "description": "Data yang diberikan tidak valid atau format tidak sesuai",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 400,
#                         "error": "Bad Request",
#                         "message": "Data yang diberikan tidak valid atau format tidak sesuai."
#                     }
#                 }
#             }
#         },
#         status.HTTP_403_FORBIDDEN: {
#             "description": "Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 403,
#                         "error": "Forbidden",
#                         "message": "Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini."
#                     }
#                 }
#             }
#         },
#         status.HTTP_404_NOT_FOUND: {
#             "description": "Alamat tidak ditemukan berdasarkan ID yang diberikan",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 404,
#                         "error": "Not Found",
#                         "message": "Alamat dengan ID yang diberikan tidak ditemukan."
#                     }
#                 }
#             }
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "description": "Kesalahan server saat memperbarui data berat pengiriman",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 500,
#                         "error": "Internal Server Error",
#                         "message": "Kesalahan tak terduga saat memperbarui data berat pengiriman."
#                     }
#                 }
#             }
#         }
#     },
#     summary="Update Data of Shipment from Account login"
# )
# def update_my_shipment(
#         update_request: shipment_dtos.ShipmentIdToUpdateDto,
#         request: shipment_dtos.RequestIdToUpdateDto,
#         update_data: shipment_dtos.ShipmentCreateDto,
#         jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
#         db: Session = Depends(get_db)
# ):
#     """
#     # Update Data Pengiriman #

#     Endpoint ini memungkinkan pengguna dengan akses user yang sudah login dapat untuk memperbarui informasi tujuan pengiriman berdasarkan ID alamat yang sudah disimpan sebelumnya.

#     **Parameter:**
#     - **update_request** (ShipmentIdToUpdateDto): Data ID shipment yang akan diperbarui.
#     - **update_data** (ShipmentDataUpdateDTO): Data baru untuk pengiriman.
#     - **jwt_token** (TokenPayLoad): Payload token JWT yang digunakan untuk memverifikasi akses pengguna.
    
#     **Return:**
#     - **200 OK**: Data Shipping/ pengiriman berhasil diperbarui.
#     - **400 Bad Request**: Data yang diberikan tidak valid atau format tidak sesuai.
#     - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini.
#     - **404 Not Found**: Alamat tidak ditemukan berdasarkan ID yang diberikan.
#     - **500 Internal Server Error**: Kesalahan server saat memperbarui data alamat tujuan pengiriman.
#     """
#     result = update_shipping(
#         db, 
#         update_request, 
#         request,
#         update_data, 
#         user_id=jwt_token.id
#     )

#     if result.error:
#         raise result.error

#     return result.unwrap()


@router.put(
    "/activate/{shipment_id}", 
    response_model=shipment_dtos.ShipmentActivateResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
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
    summary="Update Activation of Shipment from Account login"
)
def update_activation(
        update_request: shipment_dtos.ShipmentIdToUpdateDto,
        activate_update: shipment_dtos.UpdateActivateDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Update Aktifasi Pemilihan Data Pengiriman #

    Endpoint ini memungkinkan pengguna dengan akses user yang sudah login dapat untuk memperbarui informasi tujuan pengiriman berdasarkan ID alamat yang sudah disimpan sebelumnya.

    **Parameter:**
    - **update_request** (ShipmentIdToUpdateDto): Data ID shipment yang akan diperbarui.
    - **activate_update** (ShipmentDataActivateUpdateDTO): Data baru aktifasi untuk pengiriman.
    - **jwt_token** (TokenPayLoad): Payload token JWT yang digunakan untuk memverifikasi akses pengguna.
    
    **Return:**
    - **200 OK**: Aktifasi Shipping/ pengiriman berhasil diperbarui.
    - **400 Bad Request**: Data yang diberikan tidak valid atau format tidak sesuai.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini.
    - **404 Not Found**: Alamat tidak ditemukan berdasarkan ID yang diberikan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui data alamat tujuan pengiriman.
    """
    result = update_activate(
        db, 
        update_request, 
        activate_update, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.delete(
    "/delete/{shipment_id}",
    response_model=shipment_dtos.DeleteShipmentInfoResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
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
    summary="Delete One Data of Shipment"
)
def delete_my_shipping_data(
        request_delete: shipment_dtos.ShipmentIdToUpdateDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Delete Data Pengiriman #

    Endpoint ini digunakan untuk menghapus produk tertentu dari wishlist pengguna.

    **Parameter:**
    - **request_delete** (DeleteShippingDto): Data ID shipment yang akan dihapus.
    - **jwt_token** (TokenPayLoad): Token payload yang memberikan akses ke data pengguna.
    - **db** (Session): Koneksi database untuk menghapus data address.

    **Return:**
    - **200 OK**: Berhasil menghapus item.
    - **404 Not Found**: Item address tidak ditemukan.
    - **403 Forbidden**: Pengguna tidak diizinkan untuk menghapus item.
    - **500 Internal Server Error**: Kesalahan tak terduga saat menghapus item.
    
    """
    result = delete_shipment(
        db, 
        request_delete, 
        jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()

from fastapi import APIRouter, Depends, status

from typing import List, Annotated

from sqlalchemy.orm import Session

from app.dtos import courier_dtos
from app.services import courier_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/courier",
    tags=["Courier Shipping"]
)

@router.post(
    "/shipping-cost",
    status_code=status.HTTP_201_CREATED,
    response_model=courier_dtos.CourierResponseDto,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Data pengiriman berhasil disimpan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Data pengiriman berhasil disimpan",
                        "data": {
                            "shipping_id": "12345abc",
                            "courier_name": "JNE",
                            "shipping_cost": 15000,
                            "estimated_delivery_time": "2024-11-10T10:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Request tidak valid, data pengiriman tidak lengkap atau salah",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang dimasukkan tidak valid atau ada kesalahan dalam request."
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
            "description": "Terjadi kesalahan saat memproses data pengiriman",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan saat memproses data pengiriman."
                    }
                }
            }
        }
    },
    summary="Post Data of Courier to Database"
)
def get_and_save_shipping_cost(
    request_data: courier_dtos.CourierCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Menghitung dan Menyimpan Biaya Pengiriman #

    Endpoint ini menerima data pengiriman, seperti biaya dan estimasi waktu pengiriman, 
    dan menyimpannya ke dalam database setelah melakukan proses validasi dan perhitungan biaya.

    **Parameter:**
    - **request_data**: Data yang mencakup informasi pengiriman yang akan dihitung dan disimpan.
    - **jwt_token**: Token JWT yang digunakan untuk memverifikasi pengguna yang mengakses endpoint ini.

    **Return:**
    - **201 Created**: Data berhasil disimpan dan informasi pengiriman dikembalikan.
    - **400 Bad Request**: Data yang diberikan tidak valid atau ada kesalahan dalam request.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **500 Internal Server Error**: Terjadi kesalahan dalam server atau database saat memproses data pengiriman.
    """
    result = courier_services.process_shipping_cost(
        request_data, 
        jwt_token.id,
        db
    )
    
    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/my-courier",
    response_model=courier_dtos.AllCourierListResponseCreateDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Data kurir berhasil diambil",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Successfully retrieved all couriers",
                        "data": [
                            {
                                "courier_id": 1,
                                "name": "JNE",
                                "service_type": "Express",
                                "contact": "08123456789"
                            },
                            {
                                "courier_id": 2,
                                "name": "TIKI",
                                "service_type": "Regular",
                                "contact": "08234567890"
                            }
                        ]
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
        status.HTTP_404_NOT_FOUND: {
            "description": "Data kurir tidak ditemukan untuk pengguna ini",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tidak ada data kurir yang ditemukan untuk pengguna ini."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil data kurir",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat mengambil data kurir."
                    }
                }
            }
        }
    },
    summary="Get all data courier in my account"
)
async def get_my_courier(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Ambil Semua Data Kurir dari Akun Pengguna #

    Endpoint ini memungkinkan pengguna untuk mengambil semua data kurir yang terkait dengan akun mereka.
    
    **Parameter:**
    - **jwt_token** (TokenPayLoad): Payload token JWT yang berisi informasi pengguna.
    
    **Return:**
    - **200 OK**: Data kurir berhasil diambil.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **404 Not Found**: Tidak ada data kurir yang ditemukan untuk pengguna ini.
    - **500 Internal Server Error**: Kesalahan server saat mengambil data kurir.
    """
    result = courier_services.my_courier(
        db, 
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.put(
    "/edit-service/{courier_id}", 
    response_model=courier_dtos.CourierInfoUpdateResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Courier service berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Courier service successfully updated",
                        "data": {
                            "courier_id": 1,
                            "name": "JNE Express",
                            "contact_info": "081234567890",
                            "status": "Active",
                            "updated_at": "2024-10-31T12:30:00"
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
                        "message": "Data yang dikirim tidak valid."
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
        status.HTTP_404_NOT_FOUND: {
            "description": "Courier dengan ID yang diberikan tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Courier dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui layanan kurir",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui layanan kurir."
                    }
                }
            }
        }
    },
    summary="Update courier service"
)
def update_my_courier_service(
        courier_update: courier_dtos.CourierIdToUpdateDto,
        courier_data: courier_dtos.CourierDataUpdateDTO,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Perbarui Layanan Kurir #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk memperbarui layanan kurir tertentu berdasarkan ID kurir.

    **Parameter:**
    - **courier_id** (int): ID kurir yang akan diperbarui.
    - **courier_update** (CourierIdToUpdateDto): Data pembaruan ID kurir.
    - **courier_data** (CourierDataUpdateDTO): Data yang akan diperbarui untuk kurir tersebut.
    - **jwt_token** (TokenPayLoad): Token JWT pengguna untuk memastikan akses yang sah.

    **Return:**
    - **200 OK**: Layanan kurir berhasil diperbarui.
    - **400 Bad Request**: Data yang dikirim tidak valid.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **404 Not Found**: Courier dengan ID yang diberikan tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui layanan kurir.
    """
    result = courier_services.update_courier(
        db, 
        courier_update, 
        courier_data, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.put(
    "/edit-courier/{courier_id}", 
    response_model=courier_dtos.CourierInfoUpdateWeightResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Berat pengiriman berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Courier weight updated successfully",
                        "data": {
                            "courier_id": 1,
                            "new_weight": 1500,
                            "updated_at": "2024-10-31T12:45:00"
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
            "description": "Kurir tidak ditemukan berdasarkan ID yang diberikan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Kurir dengan ID yang diberikan tidak ditemukan."
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
    summary="Update courier weight information"
)
def update_my_courier(
        courier_update: courier_dtos.CourierIdToUpdateDto,
        weight_data: courier_dtos.CourierDataWeightUpdateDTO,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)
):
    """
    # Update Berat Pengiriman Kurir #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk memperbarui informasi berat pengiriman kurir berdasarkan ID kurir.

    **Parameter:**
    - **courier_update** (CourierIdToUpdateDto): Data ID kurir yang akan diperbarui.
    - **weight_data** (CourierDataWeightUpdateDTO): Data baru untuk berat pengiriman.
    - **jwt_token** (TokenPayLoad): Payload token JWT yang digunakan untuk memverifikasi akses pengguna.
    
    **Return:**
    - **200 OK**: Berat pengiriman berhasil diperbarui.
    - **400 Bad Request**: Data yang diberikan tidak valid atau format tidak sesuai.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses untuk memperbarui data ini.
    - **404 Not Found**: Kurir tidak ditemukan berdasarkan ID yang diberikan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui data berat pengiriman.
    """
    result = courier_services.update_weight(
        db, 
        courier_update, 
        weight_data, 
        user_id=jwt_token.id
    )

    if result.error:
        raise result.error

    return result.unwrap()
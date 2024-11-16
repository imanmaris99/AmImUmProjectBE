from fastapi import APIRouter, Depends, status
from typing import Annotated
from sqlalchemy.orm import Session

from app.dtos import shipment_dtos
from app.services.shipment_services import create_shipment
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

from fastapi import APIRouter, Depends, status

from typing import List

from app.services.rajaongkir_services import get_province_data, get_city_data, get_city_data_by_keyword, get_shipping_cost
from app.dtos.rajaongkir_dtos import ProvinceDto, AllProvincesResponseCreateDto, CityDto, AllCitiesResponseCreateDto, ShippingCostRequest, ShippingCostDto
from app.dtos.error_response_dtos import ErrorResponseDto


router = APIRouter(
    prefix="/rajaongkir",
    tags=["ThirdParty/ RajaOngkir"]
)

@router.get(
    "/provinces",
    response_model=AllProvincesResponseCreateDto,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Data tidak ditemukan ",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Data List provinsi tidak ditemukan untuk parameter yang diberikan."
                    }
                }
            }
        },
        500: {
            "description": "Server Error - Terjadi kesalahan saat mengambil data dari API RajaOngkir.",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memproses permintaan."
                    }
                }
            }
        }
    },
    summary="Get list of all Provincies"
)
def fetch_provinces():
    """
    # Menampilkan Daftar Semua Provinsi #

    Endpoint ini digunakan untuk menampilkan data semua provinsi yang ada di Database:
    
    **Return:**
    - **200 OK**: Daftar semua Provinsi berhasil diambil.
    - **404 Not Found**: Data tidak ditemukan
        - Daftar data semua Provinsi tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan di server.
        - Kesalahan tak terduga saat memproses permintaan.
        
    """ 
    result = get_province_data()
    
    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/cities", 
    response_model=AllCitiesResponseCreateDto,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "description": "Data tidak ditemukan",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Data List kota tidak ditemukan untuk parameter yang diberikan."
                    }
                }
            }
        },
        500: {
            "description": "Server Error - Terjadi kesalahan saat mengambil data dari API RajaOngkir.",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memproses permintaan."
                    }
                }
            }
        }
    },
    summary="Get list of all Cities"
)
def fetch_cities():
    """
    # Menampilkan Daftar Semua Data Kota #

    Endpoint ini digunakan untuk menampilkan data semua kota yang ada di Database:
    
    **Return:**
    - **200 OK**: Daftar semua Kota berhasil diambil.
    - **404 Not Found**: Data tidak ditemukan
        - Daftar data semua Kota tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan di server.
        - Kesalahan tak terduga saat memproses permintaan.
        
    """ 
    result = get_city_data()

    if result.error:
        raise result.error

    return result.unwrap()

@router.get(
    "/cities/by-keyword",
    response_model=AllCitiesResponseCreateDto,
    status_code=status.HTTP_200_OK,
    summary="Mencari kota berdasarkan nama"
)
async def search_cities(
    city_name: str 
) -> AllCitiesResponseCreateDto:
    """
    Endpoint untuk mencari kota berdasarkan nama. Jika tidak ada nama kota yang diberikan,
    maka akan mengembalikan semua kota.
    """
    result= get_city_data_by_keyword(city_name=city_name)

    if result.error:
        raise result.error

    return result.unwrap()

@router.post(
    "/shipping-cost", 
    response_model=ShippingCostDto,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Berhasil mengambil estimasi ongkos kirim.",
            "content": {
                "application/json": {
                    "example": {
                        "courier": "jne",
                        "details": [
                            {
                                "service": "REG",
                                "description": "Regular Service",
                                "cost": 18000,
                                "etd": "2-3"
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Parameter yang dimasukkan tidak valid.",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Parameter yang diberikan tidak valid, periksa ulang nilai origin, destination, weight, atau courier."
                    }
                }
            }
        },
        404: {
            "description": "Data tidak ditemukan - Ongkos kirim atau kota/provinsi tidak ditemukan.",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Data biaya pengiriman tidak ditemukan untuk parameter yang diberikan."
                    }
                }
            }
        },
        500: {
            "description": "Server Error - Terjadi kesalahan saat mengambil data dari API RajaOngkir.",
            "model": ErrorResponseDto,
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memproses permintaan."
                    }
                }
            }
        }
    },
    summary="Read shipping cost"
)
def read_shipping_cost(request: ShippingCostRequest):
    """
    # Perkiraan Perhitungan Biaya Kirim #

    Endpoint ini digunakan untuk menghitung ongkos kirim berdasarkan beberapa parameter.
    
    **Return:**
    - **200 OK**: Nilai ongkis pengiriman berhasil ditampilkan.
    - **400 Bad Request**: Bad Request.
        - Parameter yang dimasukkan tidak valid.
    - **404 Not Found**: Data tidak ditemukan
        - Ongkos kirim atau kota/provinsi tidak ditemukan.
    - **500 Internal Server Error**: Terjadi kesalahan di server.
        - Kesalahan tak terduga saat memproses permintaan.

    **Other:**
    - `origin`: ID atau nama kota/kabupaten asal pengiriman. Misal: id= 497 (untuk id kota Wonogiri).
    - `destination`: ID atau nama kota/kabupaten tujuan pengiriman. Misal: id= 455 (untuk id kota Tangerang).
    - `weight`: Berat barang dalam gram. Default 1000 gram (1 kg). Masukkan angka sesuai berat yang sebenarnya.
    - `courier`: Nama kurir yang digunakan. Pilih dari salah satu: 'jne', 'pos', atau 'tiki'. Default: 'jne'.
    
    Response yang diterima akan berisi estimasi ongkos kirim berdasarkan input yang diberikan.
        
    """  
    result = get_shipping_cost(
        request_data=request
    )    
        
    if result.error:
        raise result.error
    
    return result.unwrap()  
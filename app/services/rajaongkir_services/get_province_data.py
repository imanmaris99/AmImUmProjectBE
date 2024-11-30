from typing import List, Optional

from fastapi import HTTPException, status

import json

from app.utils.rajaongkir_utils import send_get_request
from app.dtos.rajaongkir_dtos import ProvinceDto, AllProvincesResponseCreateDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs.rajaongkir_config import Config
from app.libs.redis_config import redis_client

from app.utils import optional

CACHE_TTL = 3600  # 1 hour TTL for cache

# Fungsi untuk validasi respons dari API RajaOngkir
def validate_province_response(response: dict):
    if not isinstance(response, dict) or "rajaongkir" not in response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Invalid response from RajaOngkir API"
            ).dict()
        )

    provinces = response.get("rajaongkir", {}).get("results", [])
    if not provinces:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="Info provinces not found"
            ).dict()
        )

    if not isinstance(provinces, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Unexpected format in provinces data"
            ).dict()
        )

    return provinces

# Fungsi untuk mengonversi data provinsi ke dalam ProvinceDto
def parse_province_data(provinces: List[dict]) -> List[ProvinceDto]:
    province_dtos = []
    for p in provinces:
        if all(key in p for key in ("province_id", "province")):
            province_dtos.append(ProvinceDto(
                province_id=p["province_id"],
                province=p["province"]
            ))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server Error",
                    message="Unexpected data format for a province"
                ).dict()
            )
    return province_dtos

# Fungsi utama untuk mendapatkan data provinsi dari API RajaOngkir
# def get_province_data(province_id: Optional[int] = None) -> optional.Optional[AllProvincesResponseCreateDto, HTTPException]:
#     headers = {'key': Config.RAJAONGKIR_API_KEY}
#     url = "/starter/province"

#     response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)
    
#     try:
#         provinces = validate_province_response(response)
#         province_dtos = parse_province_data(provinces)

#         # return optional.build(data=province_dtos)
    
#         return optional.build(data=AllProvincesResponseCreateDto(
#             status_code=status.HTTP_200_OK,
#             message=f"All List of Provinces accessed successfully",
#             data=province_dtos
#         ))
        
#     except HTTPException as e:
#         return optional.build(error=e)


def get_province_data() -> optional.Optional[List[ProvinceDto], HTTPException]:
    try:
        # Cek apakah data kota ada di Redis
        cached_data = redis_client.get("provinces")
        if cached_data:
            # Parse data dari Redis
            province_dtos = [ProvinceDto(**province) for province in json.loads(cached_data)]
            return optional.build(data=province_dtos)
        
        headers = {'key': Config.RAJAONGKIR_API_KEY}
        url = "/starter/province"

        response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)
    
    # try:
        provinces = validate_province_response(response)
        province_dtos = parse_province_data(provinces)

        # Simpan data di Redis
        redis_client.setex(
            "cities", 
            CACHE_TTL, 
            json.dumps([city.dict() for city in province_dtos])
        )

        return optional.build(data=province_dtos)
    
        # return optional.build(data=AllProvincesResponseCreateDto(
        #     status_code=status.HTTP_200_OK,
        #     message=f"All List of Provinces accessed successfully",
        #     data=province_dtos
        # ))
        
    except HTTPException as e:
        return optional.build(error=e)

    except Exception as e:
        # Mengembalikan HTTPException dengan status 500 jika terjadi kesalahan umum
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error occurred: {str(e)}"
            ).dict()
        ))
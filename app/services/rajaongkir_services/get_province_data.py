from typing import List, Optional
from fastapi import HTTPException, status

from app.utils.rajaongkir_utils import send_get_request
from app.dtos.rajaongkir_dtos import ProvinceDto
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.rajaongkir_config import Config
from app.utils import optional

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
def get_province_data(province_id: Optional[int] = None) -> optional.Optional[List[ProvinceDto], HTTPException]:
    headers = {'key': Config.RAJAONGKIR_API_KEY}
    url = "/starter/province"

    response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)
    
    try:
        provinces = validate_province_response(response)
        province_dtos = parse_province_data(provinces)
        return optional.build(data=province_dtos)
        
    except HTTPException as e:
        return optional.build(error=e)


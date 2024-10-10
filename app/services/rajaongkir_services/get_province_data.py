from typing import List, Optional
from fastapi import HTTPException, status
from app.utils.rajaongkir_utils import send_get_request, send_post_request
from app.dtos.rajaongkir_dtos import ProvinceDto, ShippingCostDto, ShippingCostDetailDto
from app.libs.rajaongkir_config import Config
from app.utils import optional

def get_province_data(province_id: Optional[int] = None) -> optional.Optional[List[ProvinceDto], HTTPException]:
    """Mengambil data provinsi dari API RajaOngkir."""
    headers = {
        'key': Config.RAJAONGKIR_API_KEY
    }

    url = "/starter/province"

    response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)

    # Cek apakah respons dari API adalah format yang diharapkan
    if not isinstance(response, dict) or "rajaongkir" not in response:        
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message="Invalid response from RajaOngkir API"
        ))
    
    provinces = response.get("rajaongkir", {}).get("results", [])

    if not provinces:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message="No provinces found"
        ))
    
    # Cek apakah provinces adalah list dan bukan string
    if not isinstance(provinces, list):
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message="Unexpected format in provinces data"
        ))

    # Membuat DTO untuk setiap provinsi
    province_dtos = []
    for p in provinces:
        if isinstance(p, dict) and "province_id" in p and "province" in p:
            province_dtos.append(ProvinceDto(province_id=p["province_id"], province=p["province"]))
        else:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Unexpected data format for a province"
            ))

    return optional.build(data=province_dtos)
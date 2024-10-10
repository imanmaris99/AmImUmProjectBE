from typing import List, Optional
from fastapi import HTTPException, status
from app.utils.rajaongkir_utils import send_get_request, send_post_request
from app.dtos.rajaongkir_dtos import CityDto, ShippingCostDto, ShippingCostDetailDto
from app.libs.rajaongkir_config import Config
from app.utils import optional

def get_city_data() -> optional.Optional[List[CityDto], HTTPException]:
    """Mengambil data kota dari API RajaOngkir."""
    headers = {
        'key': Config.RAJAONGKIR_API_KEY
    }

    url = "/starter/city"

    response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)

    # Cek apakah respons dari API adalah format yang diharapkan
    if not isinstance(response, dict) or "rajaongkir" not in response:        
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message="Invalid response from RajaOngkir API"
        ))
    
    cities = response.get("rajaongkir", {}).get("results", [])

    if not cities:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message="No cities found"
        ))
    
    # Cek apakah provinces adalah list dan bukan string
    if not isinstance(cities, list):
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message="Unexpected format in cities data"
        ))

    # Membuat DTO untuk setiap kota
    city_dtos = []
    for c in cities:
        if isinstance(c, dict) and "city_id" in c and "province_id" in c and "province" in c and "type" in c and "city_name" in c and "postal_code" in c:
            city_dtos.append(CityDto(
                city_id=c["city_id"],
                province_id=c["province_id"],
                province=c["province"],
                type=c["type"],
                city_name=c["city_name"],
                postal_code=c["postal_code"]
            ))
        else:
            return optional.build(error=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Unexpected data format for a province"
            ))

    return optional.build(data=city_dtos)
from typing import List

import json 

from fastapi import HTTPException, status

from app.utils.rajaongkir_utils import send_get_request
from app.dtos.rajaongkir_dtos import CityDto, AllCitiesResponseCreateDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs.rajaongkir_config import Config
from app.libs.redis_config import custom_json_serializer, redis_client

from app.utils import optional

CACHE_TTL = 3600  # 1 hour TTL for cache


# Fungsi untuk validasi respons dari API RajaOngkir
def validate_response(response: dict):
    if not isinstance(response, dict) or "rajaongkir" not in response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Invalid response from RajaOngkir API"
            ).dict()
        )

    cities = response.get("rajaongkir", {}).get("results", [])
    if not cities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="Info about cities not found"
            ).dict()
        )

    if not isinstance(cities, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Unexpected format in cities data"
            ).dict()
        )

    return cities

# Fungsi untuk mengonversi data kota ke dalam CityDto
def parse_city_data(cities: List[dict]) -> List[CityDto]:
    city_dtos = []
    for c in cities:
        if all(key in c for key in ("city_id", "province_id", "province", "type", "city_name", "postal_code")):
            city_dtos.append(CityDto(
                city_id=c["city_id"],
                province_id=c["province_id"],
                province=c["province"],
                type=c["type"],
                city_name=c["city_name"],
                postal_code=c["postal_code"]
            ))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server Error",
                    message="Unexpected data format for a city"
                ).dict()
            )
    return city_dtos

# Fungsi utama untuk mendapatkan data kota dari API RajaOngkir
# def get_city_data() -> optional.Optional[AllCitiesResponseCreateDto, HTTPException]:
#     headers = {'key': Config.RAJAONGKIR_API_KEY}
#     url = "/starter/city"

#     response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)
    
#     try:
#         cities = validate_response(response)
#         city_dtos = parse_city_data(cities)

#         # return optional.build(data=city_dtos)

#         return optional.build(data=AllCitiesResponseCreateDto(
#             status_code=status.HTTP_200_OK,
#             message=f"All List of Cities accessed successfully",
#             data=city_dtos
#         ))
        
#     except HTTPException as e:
#         return optional.build(error=e)
    
def get_city_data() -> optional.Optional[List[CityDto], HTTPException]:
    try:
        # Cek apakah data kota ada di Redis
        cached_data = redis_client.get("cities")
        if cached_data:
            # Parse data dari Redis
            city_dtos = [CityDto(**city) for city in json.loads(cached_data)]
            return optional.build(data=city_dtos)
        
        headers = {'key': Config.RAJAONGKIR_API_KEY}
        url = "/starter/city"

        response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)
    
    # try:
        cities = validate_response(response)
        city_dtos = parse_city_data(cities)

        # Simpan data di Redis
        redis_client.setex(
            "cities", 
            CACHE_TTL, 
            json.dumps([city.dict() for city in city_dtos])
        )

        return optional.build(data=city_dtos)

        # return optional.build(data=AllCitiesResponseCreateDto(
        #     status_code=status.HTTP_200_OK,
        #     message=f"All List of Cities accessed successfully",
        #     data=city_dtos
        # ))
        
    except HTTPException as e:
        return optional.build(error=e)

def get_city_data_by_keyword(city_name: str = None) -> optional.Optional[AllCitiesResponseCreateDto, HTTPException]:
    try:
        # Ambil data kota dari Redis
        cached_data = redis_client.get("cities")
        if cached_data:
            city_dtos = [CityDto(**city) for city in json.loads(cached_data)]
        else:
    
            headers = {'key': Config.RAJAONGKIR_API_KEY}
            url = "/starter/city"

            response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)
        
        # try:
            cities = validate_response(response)
            city_dtos = parse_city_data(cities)

            # Simpan data di Redis
            redis_client.setex(
                "cities", 
                CACHE_TTL, 
                json.dumps([city.dict() for city in city_dtos])
            )
            
        # Jika ada city_name, filter kota berdasarkan nama
        if city_name:
            city_dtos = [city for city in city_dtos if city.city_name.lower() == city_name.lower()]

            if not city_dtos:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_404_NOT_FOUND,
                        error="Not Found",
                        message=f"Kota dengan nama '{city_name}' tidak ditemukan"
                    ).dict()
                )

        return optional.build(data=AllCitiesResponseCreateDto(
            status_code=status.HTTP_200_OK,
            message="Daftar kota berhasil diakses",
            data=city_dtos
        ))

    except HTTPException as e:
        return optional.build(error=e)
from typing import List

import json

from fastapi import HTTPException, status

from app.utils.rajaongkir_utils import send_get_request
from app.dtos.rajaongkir_dtos import CityDto
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.rajaongkir_config import Config
from app.libs.redis_config import redis_client
from app.utils import optional

CACHE_TTL = 3600


def validate_response(response: dict):
    if not isinstance(response, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Invalid response from RajaOngkir API"
            ).dict()
        )

    cities = response.get("data", [])
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


def parse_city_data(cities: List[dict]) -> List[CityDto]:
    city_dtos = []
    for c in cities:
        city_id = c.get("id") or c.get("city_id") or c.get("cityId")
        province_id = c.get("province_id") or c.get("provinceId")
        province_name = (
            c.get("province")
            or c.get("province_name")
            or c.get("provinceName")
            or ""
        )
        city_name = (
            c.get("city_name")
            or c.get("city")
            or c.get("name")
            or c.get("label")
            or c.get("text")
            or ""
        )
        postal_code = c.get("zip_code") or c.get("postal_code") or c.get("postalCode") or 0
        city_type = c.get("type") or c.get("city_type") or "city"

        if city_id is not None and province_id is not None and city_name:
            city_dtos.append(CityDto(
                city_id=int(city_id),
                province_id=int(province_id),
                province=str(province_name),
                type=str(city_type),
                city_name=str(city_name),
                postal_code=int(postal_code),
            ))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server Error",
                    message=f"Unexpected data format for a city: {c}"
                ).dict()
            )
    return city_dtos


def get_city_data(province_id: int) -> optional.Optional[List[CityDto], HTTPException]:
    try:
        cache_key = f"cities:{province_id}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            city_dtos = [CityDto(**city) for city in json.loads(cached_data)]
            return optional.build(data=city_dtos)

        headers = {'key': Config.RAJAONGKIR_API_KEY}
        url = f"{Config.RAJAONGKIR_API_BASE_PATH}/destination/city/{province_id}"
        response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)

        cities = validate_response(response)
        city_dtos = parse_city_data(cities)

        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps([city.dict() for city in city_dtos])
        )

        return optional.build(data=city_dtos)

    except HTTPException as e:
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error occurred: {str(e)}"
            ).dict()
        ))

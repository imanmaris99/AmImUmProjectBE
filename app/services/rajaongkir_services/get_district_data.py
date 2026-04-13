from typing import List

import json

from fastapi import HTTPException, status

from app.utils.rajaongkir_utils import send_get_request
from app.dtos.rajaongkir_dtos import DistrictDto
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

    districts = response.get("data", [])
    if not districts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="Info about districts not found"
            ).dict()
        )

    if not isinstance(districts, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Unexpected format in districts data"
            ).dict()
        )

    return districts


def parse_district_data(districts: List[dict]) -> List[DistrictDto]:
    district_dtos = []
    for district in districts:
        district_id = district.get("id")
        district_name = district.get("district_name") or district.get("subdistrict_name") or district.get("label")
        if district_id is not None and district_name:
            district_dtos.append(DistrictDto(
                district_id=district_id,
                district=district_name,
            ))
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server Error",
                    message="Unexpected data format for a district"
                ).dict()
            )
    return district_dtos


def get_district_data(city_id: int) -> optional.Optional[List[DistrictDto], HTTPException]:
    try:
        cache_key = f"districts:{city_id}"
        cached_data = redis_client.get(cache_key)
        if cached_data:
            district_dtos = [DistrictDto(**district) for district in json.loads(cached_data)]
            return optional.build(data=district_dtos)

        headers = {'key': Config.RAJAONGKIR_API_KEY}
        url = f"{Config.RAJAONGKIR_API_BASE_PATH}/destination/district/{city_id}"
        response = send_get_request(Config.RAJAONGKIR_API_HOST, url, headers)

        districts = validate_response(response)
        district_dtos = parse_district_data(districts)

        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps([district.dict() for district in district_dtos])
        )

        return optional.build(data=district_dtos)

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

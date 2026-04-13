import hashlib
from fastapi import HTTPException, status

import json

from app.dtos.rajaongkir_dtos import ShippingCostRequest, ShippingCostDto, ShippingCostDetailDto
from app.dtos.error_response_dtos import ErrorResponseDto

from app.libs.rajaongkir_config import Config
from app.libs.redis_config import redis_client

from app.utils.rajaongkir_utils import send_post_request
from app.utils import optional

# Fungsi untuk validasi respons dari API RajaOngkir/Komerce
def validate_shipping_cost_response(response: dict):
    if not isinstance(response, dict) or "meta" not in response:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message="Invalid response from RajaOngkir API"
            ).dict()
        )

    meta = response.get("meta") or {}
    if meta.get("code") != 200:
        raise HTTPException(
            status_code=meta.get("code", status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail=ErrorResponseDto(
                status_code=meta.get("code", status.HTTP_500_INTERNAL_SERVER_ERROR),
                error="API Error",
                message=meta.get("message", "Unknown error occurred.")
            ).dict()
        )

    results = response.get("data") or []
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="No shipping cost data found."
            ).dict()
        )

    return results

# Fungsi untuk parsing detail biaya pengiriman ke DTO
def parse_shipping_cost_details(details: list) -> list[ShippingCostDetailDto]:
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponseDto(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="No shipping cost details data found."
            ).dict()
        )

    return [
        ShippingCostDetailDto(
            service=d["service"],
            description=d["description"],
            cost=d["cost"],
            etd=d["etd"]
        )
        for d in details
    ]

# Fungsi utama untuk mendapatkan biaya pengiriman dari API RajaOngkir
def get_shipping_cost(request_data: ShippingCostRequest) -> optional.Optional[ShippingCostDto, HTTPException]:
    headers = {
        'key': Config.RAJAONGKIR_API_KEY,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    body = {
        "origin": str(request_data.origin),
        "destination": str(request_data.destination),
        "weight": str(request_data.weight),
        "courier": request_data.courier
    }

    # Buat key unik untuk Redis berdasarkan request data
    redis_key = f"shipping_cost:{hashlib.md5(str(body).encode()).hexdigest()}"

    try:
        # Cek apakah data tersedia di Redis
        cached_data = redis_client.get(redis_key)
        if cached_data:
            # Jika data ditemukan, kembalikan dari cache
            return optional.build(data=ShippingCostDto.parse_raw(cached_data))
        
        # Kirim permintaan POST ke API RajaOngkir
        response = send_post_request(
            Config.RAJAONGKIR_API_HOST,
            f"{Config.RAJAONGKIR_API_BASE_PATH}/calculate/domestic-cost",
            headers,
            body,
            encode_json=False
        )

        courier_data = validate_shipping_cost_response(response)
        shipping_details = parse_shipping_cost_details(courier_data)

        shipping_cost_dto = ShippingCostDto(
            courier=request_data.courier,
            details=shipping_details
        )

        # Simpan data ke Redis dengan TTL (Time To Live)
        redis_client.setex(redis_key, 3600, shipping_cost_dto.json())  # TTL = 1 jam

        return optional.build(data=shipping_cost_dto)


    except HTTPException as e:
        # Meneruskan pengecualian HTTP yang sudah ditangani di atas
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

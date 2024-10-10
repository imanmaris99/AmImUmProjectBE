from typing import List, Optional
from fastapi import HTTPException, status
from app.utils.rajaongkir_utils import send_get_request, send_post_request
from app.dtos.rajaongkir_dtos import ProvinceDto, ShippingCostDto, ShippingCostDetailDto
from app.libs.rajaongkir_config import Config
from app.utils import optional 


def get_shipping_cost(origin: int, destination: int, weight: int, courier: str) -> optional.Optional[ShippingCostDto, HTTPException]:
    """Mengambil biaya pengiriman dari API RajaOngkir berdasarkan asal, tujuan, berat, dan kurir."""
    headers = {
        'key': Config.RAJAONGKIR_API_KEY,
        'Content-Type': 'application/json'
    }

    body = {
        "origin": origin,
        "destination": destination,
        "weight": weight,
        "courier": courier
    }

    response = send_post_request(Config.RAJAONGKIR_API_HOST, "/starter/cost", headers, body)
    results = response.get("rajaongkir", {}).get("results", [])

    if not results:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message="No shipping cost data found"
        ))
    
    courier_data = results[0]
    details = courier_data.get("costs", [])

    if not details:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            messager="No shipping cost details found"
        ))

    shipping_details = [
        ShippingCostDetailDto(
            service=d["service"],
            description=d["description"],
            cost=d["cost"][0]["value"],
            etd=d["cost"][0]["etd"]
        ) for d in details
    ]

    return optional.build(data=ShippingCostDto(courier=courier_data["name"], details=shipping_details))
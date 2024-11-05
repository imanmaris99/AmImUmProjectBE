from typing import Optional

from fastapi import HTTPException, status

from app.utils.rajaongkir_utils import send_post_request
from app.dtos.rajaongkir_dtos import ShippingCostRequest, ShippingCostDto, ShippingCostDetailDto
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.rajaongkir_config import Config
from app.utils import optional


def get_shipping_cost(
        request_data: ShippingCostRequest
    ) -> optional.Optional[ShippingCostDto, HTTPException]:
    """Mengambil biaya pengiriman dari API RajaOngkir berdasarkan asal, tujuan, berat, dan kurir."""
    
    headers = {
        'key': Config.RAJAONGKIR_API_KEY,
        'Content-Type': 'application/json'
    }

    body = {
        "origin": request_data.origin,
        "destination": request_data.destination,
        "weight": request_data.weight,
        "courier": request_data.courier
    }

    try:
        # Kirim permintaan POST ke API RajaOngkir
        response = send_post_request(
            Config.RAJAONGKIR_API_HOST, 
            "/starter/cost", 
            headers, 
            body
        )

        results = response.get("rajaongkir", {}).get("results", [])

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No shipping cost data found."
                ).dict()
            )

        courier_data = results[0]
        details = courier_data.get("costs", [])

        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="No shipping cost details data found."
                ).dict()
            )

        # Mapping data dari API ke DTO
        shipping_details = [
            ShippingCostDetailDto(
                service=d["service"],
                description=d["description"],
                cost=d["cost"][0]["value"],
                etd=d["cost"][0]["etd"]
            ) for d in details if d.get("cost")
        ]

        return optional.build(data=ShippingCostDto(courier=courier_data["name"], details=shipping_details))

    except HTTPException as e:
        # Meneruskan pengecualian HTTP yang ditangani di atas
        raise e  # Menggunakan `raise` untuk meneruskan exception

    except Exception as e:
        # Mengembalikan HTTPException dengan status 500 jika terjadi kesalahan
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error occurred: {str(e)}"
            ).dict()
        )

# def get_shipping_cost(
#         origin: int, destination: int, weight: int, courier: str
#     ) -> optional.Optional[ShippingCostDto, HTTPException]:
#     """Mengambil biaya pengiriman dari API RajaOngkir berdasarkan asal, tujuan, berat, dan kurir."""
#     headers = {
#         'key': Config.RAJAONGKIR_API_KEY,
#         'Content-Type': 'application/json'
#     }

#     body = {
#         "origin": origin,
#         "destination": destination,
#         "weight": weight,
#         "courier": courier
#     }

#     response = send_post_request(Config.RAJAONGKIR_API_HOST, "/starter/cost", headers, body)
#     results = response.get("rajaongkir", {}).get("results", [])

#     if not results:
#         return optional.build(error= HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=ErrorResponseDto(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 error="Not Found",
#                 message="No shipping cost data found"
#             ).dict()
#         ))
#         # return optional.build(error=HTTPException(
#         #     status_code=status.HTTP_404_NOT_FOUND,
#         #     error="Not Found",
#         #     message="No shipping cost data found"
#         # ))
    
#     courier_data = results[0]
#     details = courier_data.get("costs", [])

#     if not details:
#         return optional.build(error= HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=ErrorResponseDto(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 error="Not Found",
#                 message="No shipping cost details data found"
#             ).dict()
#         ))
#         # return optional.build(error=HTTPException(
#         #     status_code=status.HTTP_404_NOT_FOUND,
#         #     error="Not Found",
#         #     messager="No shipping cost details found"
#         # ))

#     shipping_details = [
#         ShippingCostDetailDto(
#             service=d["service"],
#             description=d["description"],
#             cost=d["cost"][0]["value"],
#             etd=d["cost"][0]["etd"]
#         ) for d in details
#     ]

#     return optional.build(data=ShippingCostDto(courier=courier_data["name"], details=shipping_details))
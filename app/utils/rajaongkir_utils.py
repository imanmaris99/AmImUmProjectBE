import http.client
import json

from fastapi import HTTPException, status

from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.rajaongkir_config import Config



def send_get_request(host: str, url: str, headers: dict):
    """Mengirimkan permintaan GET ke server RajaOngkir dan menangani responsnya."""
    try:
        conn = http.client.HTTPSConnection(host)
        conn.request("GET", url, headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        result = json.loads(data.decode("utf-8"))

        if response.status != 200:
            raise HTTPException(
                status_code=response.status,
                detail=ErrorResponseDto(
                    status_code=response.status,
                    error="API Error",
                    message=result.get("rajaongkir", {}).get("status", {}).get("description", "Unknown error occurred.")
                ).dict()
                # error="API Error",
                # message=result.get("rajaongkir", {}).get("status", {}).get("description", "Unknown error occurred.")
            )

        return result

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Invalid Response",
                    message="Failed to decode JSON from RajaOngkir API."
                ).dict()
            # error="Invalid Response",
            # message="Failed to decode JSON from RajaOngkir API."
        )

    except HTTPException as e:
        # Meneruskan pengecualian HTTP yang ditangani di atas
        raise e  # Menggunakan `raise` untuk meneruskan exception

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server",
                    message=f"Error occurred during API request: {str(e)}"
                ).dict()
            # error="Internal Server Error",
            # message=f"Error occurred during API request: {str(e)}"
        )


def send_post_request(host: str, url: str, headers: dict, body: dict):
    """Mengirimkan permintaan POST ke server RajaOngkir dan menangani responsnya."""
    try:
        conn = http.client.HTTPSConnection(host)
        conn.request("POST", url, body=json.dumps(body), headers=headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        result = json.loads(data.decode("utf-8"))

        if response.status != 200:
            raise HTTPException(
                status_code=response.status,
                detail=ErrorResponseDto(
                    status_code=response.status,
                    error="API Error",
                    message=result.get("rajaongkir", {}).get("status", {}).get("description", "Unknown error occurred.")
                ).dict()
            )
            # raise HTTPException(
            #     status_code=response.status,
            #     error="API Error",
            #     message=result.get("rajaongkir", {}).get("status", {}).get("description", "Unknown error occurred.")
            # )

        return result

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Invalid Response",
                    message="Failed to decode JSON from RajaOngkir API."
                ).dict()
        )
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     error="Invalid Response",
        #     message="Failed to decode JSON from RajaOngkir API."
        # )

    except HTTPException as e:
        # Meneruskan pengecualian HTTP yang ditangani di atas
        raise e  # Menggunakan `raise` untuk meneruskan exception

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error="Internal Server",
                    message=f"Error occurred during API request: {str(e)}"
                ).dict()
        )
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     error="Internal Server Error",
        #     message=f"Error occurred during API request: {str(e)}"
        # )

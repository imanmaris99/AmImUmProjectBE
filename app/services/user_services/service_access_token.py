from app.libs.jwt_lib import jwt_dto, jwt_service
from fastapi import HTTPException, status

def service_access_token(user_id: str):
    # Memastikan user_id tidak kosong
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error": "Bad Request",
                "message": "User ID must not be empty."
            }
        )

    # Mempersiapkan data user untuk token
    user_data = {
        "id": user_id
    }

    try:
        # Membuat access token menggunakan layanan JWT
        access_token = jwt_service.create_access_token(user_data)
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    except Exception as e:
        # Menangani error dalam proses pembuatan token
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Internal Server Error",
                "message": f"Failed to create access token: {str(e)}"
            }
        )


















# from app.libs.jwt_lib import jwt_dto, jwt_service


# def service_access_token(user_id: str):
#     user_ditch = dict([
#         ("id", user_id)
#     ])
#     return jwt_service.create_access_token(user_ditch)

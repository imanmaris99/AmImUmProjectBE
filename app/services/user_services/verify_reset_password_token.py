from fastapi import HTTPException, status
from firebase_admin import auth


def verify_reset_password_token(token: str):
    """
    Service untuk memverifikasi token reset password dari Firebase.
    """
    try:
        decoded_token = auth.verify_id_token(token)
        email = decoded_token['email']
        return email

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error": "Bad Request",
                "message": "Token reset password tidak valid atau sudah kedaluwarsa. Silakan minta link reset baru."
            },
        )

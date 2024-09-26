# user_services.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from firebase_admin import auth

from app.models.user_model import UserModel
from app.utils.firebase_utils import send_email_reset_password


def send_reset_password_request(db: Session, email: str):
    # Cari pengguna di database berdasarkan email
    user = db.query(UserModel).filter(UserModel.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found."
        )

    try:
        # Generate tautan reset password dari Firebase
        reset_link = auth.generate_password_reset_link(email)

        # Kirim email reset password ke pengguna
        send_email_reset_password(email, reset_link)
        
        return {"message": "Password reset email has been sent."}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Failed to send reset password email: {str(e)}"
        )

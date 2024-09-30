from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from firebase_admin import auth
from app.dtos.user_dtos import ResetPasswordDto
from app.libs import password_lib
from app.models.user_model import UserModel
from app.services.user_services import verify_reset_password_token
from app.utils.error_parser import is_valid_password

def reset_password(payload: ResetPasswordDto, db: Session):
    # Verifikasi token Firebase
    email = verify_reset_password_token(payload.oob_code)

    if email != payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Bad Request",
            message="Email in token does not match the provided email."
        )

    # Validasi password baru
    is_valid, error_message = is_valid_password(payload.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Bad Request",
            message=error_message
        )

    # Cari pengguna berdasarkan email
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message="User not found"
        )

    try:
        # Hash password baru dan simpan ke database
        user.password = password_lib.get_password_hash(payload.new_password)  # Gantilah sesuai nama field password di model Anda
        db.commit()

        return {"message": "Password has been reset successfully."}
    
    except Exception as e:
        db.rollback()  # Rollback jika ada error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"Failed to reset password: {str(e)}"
        )

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.dtos import user_dtos
from app.utils import optional
from firebase_admin import auth
from app.models.user_model import UserModel
from app.utils.firebase_utils import send_email_reset_password
from app.libs.verification_code import generate_verification_code

ALLOWED_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

def is_allowed_email_domain(email: str) -> bool:
    domain = email.split('@')[-1]
    return domain in ALLOWED_DOMAINS

def send_reset_password_request(db: Session, payload: user_dtos.ForgotPasswordDto):
    # Validasi domain email
    if not is_allowed_email_domain(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error": "Bad Request",
                "message": "Supported email domains are: " + ', '.join(ALLOWED_DOMAINS)
            }
        )

    # Cari user di database
    user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status_code": status.HTTP_404_NOT_FOUND,
                "error": "Not Found",
                "message": f"Email {payload.email} not found."
            }
        )

    try:
        # Verifikasi keberadaan user di Firebase
        auth.get_user_by_email(payload.email)

        # Generate kode verifikasi reset password
        verification_code = generate_verification_code()
        user.verification_code = verification_code
        db.commit()

        # Buat link reset password menggunakan kode verifikasi kustom
        reset_link = f"https://amimumprojectbe-production.up.railway.app/user/password-reset/confirm?email={payload.email}&code={verification_code}"

        # Kirim email reset password
        send_email_reset_password(payload.email, verification_code, reset_link)

        return optional.build(data=user_dtos.ForgotPasswordResponseDto(
            status_code=status.HTTP_200_OK,
            message=f"Password reset email has been sent in this email {payload.email}.",
            data=payload
        ))

    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "status_code": status.HTTP_404_NOT_FOUND,
                "error": "Not Found",
                "message": "User not found in Firebase."
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": "Internal Server Error",
                "message": f"Unexpected error occurred: {str(e)}"
            }
        )




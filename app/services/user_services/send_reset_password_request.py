from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.dtos import user_dtos
from app.utils import optional
from firebase_admin import auth

from app.models.user_model import UserModel
from app.utils.firebase_utils import send_email_reset_password

ALLOWED_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}  # Tambahkan domain yang didukung

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
                "message": (
                    f"The provided email domain is not supported."
                    f"Supported email domains are: {', '.join(ALLOWED_DOMAINS)}"
                )
            }
        )
    
    # Cari pengguna di database berdasarkan email
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
        # Pastikan pengguna terdaftar di Firebase
        firebase_user = auth.get_user_by_email(payload.email)

        # Buat link reset password dari Firebase
        reset_link = auth.generate_password_reset_link(payload.email)

        # Kirim email reset password ke pengguna dengan penanganan error tambahan
        try:
            send_email_reset_password(payload.email, reset_link)
        except ConnectionError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "error": "Internal Server Error",
                    "message": "Connection to email server failed. Please try again later."
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "error": "Internal Server Error",
                    "message": f"Failed to send reset password email: {str(e)}"
                }
            )

        # Respons sukses jika email berhasil dikirim
        return optional.build(data=user_dtos.ForgotPasswordResponseDto(
            status_code=status.HTTP_200_OK,
            message="Password reset email has been sent.",
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


















# from sqlalchemy.orm import Session
# from fastapi import HTTPException, status
# from app.dtos import user_dtos
# from app.utils import optional
# from firebase_admin import auth

# from app.models.user_model import UserModel
# from app.utils.firebase_utils import send_email_reset_password

# # from app.utils.logging_utils import log_password_reset_request


# def send_reset_password_request(db: Session, payload: user_dtos.ForgotPasswordDto):
#     # Cari pengguna di database berdasarkan email
#     user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    
#     if not user:
#         # log_password_reset_request(email, "Failed - User not found")
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail={
#                 "status_code": status.HTTP_404_NOT_FOUND,
#                 "error": "Not Found",
#                 "message": f"Email {payload.email} not found."
#             }
#         )

#     try:
#         # Pastikan pengguna terdaftar di Firebase
#         firebase_user = auth.get_user_by_email(payload.email)

#         # Buat link reset password dari Firebase
#         reset_link = auth.generate_password_reset_link(payload.email)

#         # Kirim email reset password ke pengguna
#         send_email_reset_password(payload.email, reset_link)

#         # log_password_reset_request(email, "Success")
#         return optional.build(data=user_dtos.ForgotPasswordResponseDto(
#             status_code=status.HTTP_200_OK,
#             message="Password reset email has been sent.",
#             data=payload
#         ))

#     except auth.UserNotFoundError:  # Handle error jika pengguna tidak ditemukan di Firebase
#         # log_password_reset_request(email, "Failed - User not found in Firebase")
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail={
#                 "status_code": status.HTTP_404_NOT_FOUND,
#                 "error": "Not Found",
#                 "message": "User not found in Firebase."
#             }
#         )

#     except Exception as e:
#         # log_password_reset_request(email, f"Failed - {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail={
#                 "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 "error": "Internal Server Error",
#                 "message": f"Failed to send reset password email: {str(e)}"
#             }
#         )




# def send_reset_password_request(db: Session, payload: user_dtos.ForgotPasswordDto):
#     # Cari pengguna di database berdasarkan email
#     user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    
#     if not user:
#         # log_password_reset_request(email, "Failed - User not found")
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             error="Not Found",
#             message="Email not found."
#         )

#     try:
#         # Ensure the user is registered in Firebase
#         firebase_user = auth.get_user_by_email(payload.email)

#         # Generate password reset link from Firebase
#         reset_link = auth.generate_password_reset_link(payload.email)

#         # Send password reset email to the user
#         send_email_reset_password(payload.email, reset_link)

#         # log_password_reset_request(email, "Success")
#         return optional.build(data=user_dtos.ForgotPasswordResponseDto(
#             status_code=200,
#             message="Password reset email has been sent.",
#             data=payload
#         ))

#     except auth.UserNotFoundError:  # Handle error jika pengguna tidak ditemukan di Firebase
#         # log_password_reset_request(email, "Failed - User not found in Firebase")
#         return  optional.build(error=HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             error="Not Found",
#             message="User not found in Firebase."
#         ))

#     except Exception as e:
#         # log_password_reset_request(email, f"Failed - {str(e)}")
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message=f"Failed to send reset password email: {str(e)}"
#         ))

# from typing import Type
# import jwt
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, UploadFile, status

# from app.models.user_model import UserModel
# from app.dtos import user_dtos

# from app.libs import password_lib
# from app.libs.jwt_lib import jwt_service
# from app.utils import optional, error_parser

# from .get_by_user_email import get_user_by_email



# def reset_password(db: Session, token: str, new_password: str):
#     try:
#         # Verifikasi token dan ambil email
#         email = jwt_service.verify_reset_password_token(token)
#     except jwt.ExpiredSignatureError:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             error="Bad Request",
#             message="The reset token has expired. Please request a new reset password."
#         ))
#     except jwt.InvalidTokenError:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             error="Bad Request",
#             message="The reset token is invalid."
#         ))

#     # Cek apakah email yang diberikan ada di database
#     user_optional = get_user_by_email(db, email)

#     if user_optional.error:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             error="Not Found",
#             message="User with the provided email does not exist."
#         ))

#     user_model = user_optional.data

#     # Cek jika akun pengguna diblokir atau tidak aktif
#     if not user_model.is_active:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             error="Forbidden",
#             message="Your account is not active. Please contact support."
#         ))

#     # Hash dan set password baru
#     hashed_password = password_lib.hash_password(new_password)
#     user_model.hash_password = hashed_password

#     # Simpan perubahan ke database
#     db.commit()

#     return {"message": "Password has been reset successfully."}

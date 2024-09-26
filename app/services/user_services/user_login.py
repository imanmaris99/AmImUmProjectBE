from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.dtos import user_dtos
from app.utils import optional
from app.models.user_model import UserModel
from app.libs import password_lib
from app.utils.firebase_utils import authenticate_firebase_user
from .get_by_user_email import get_user_by_email


def user_login(db: Session, user: user_dtos.UserLoginPayloadDto) -> optional.Optional[UserModel, Exception]:
    # Validasi input user, jika email atau password kosong kembalikan 400 Bad Request
    if not user.email or not user.password:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Bad Request",
            message="Email and password must be provided."
        ))

    try:
        # Autentikasi dengan Firebase
        firebase_user = authenticate_firebase_user(user.email, user.password)

        # Cek apakah pengguna ada di database lokal
        user_optional = get_user_by_email(db, user.email)
        
        if user_optional.error:
            # Jika user tidak ditemukan di database lokal, kembalikan error
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Not Found",
                message="User with the provided email does not exist."
            ))

        user_model = user_optional.data  # Mengambil data user dari Optional

        # Cek apakah akun pengguna diblokir atau tidak aktif
        if not user_model.is_active:  # Misalkan ada atribut is_active di model User
            return optional.build(error=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                error="Forbidden",
                message="Your account is not active. Please contact support."
            ))

        # Verifikasi password (Firebase sudah memverifikasi password di langkah sebelumnya)
        if not password_lib.verify_password(plain_password=user.password, hashed_password=user_model.hash_password):
            return optional.build(error=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Un Authorization",
                message="Password does not match."
            ))

        # Proses selanjutnya, misalnya generate JWT token
        return optional.build(data=user_model)

    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An unexpected error occurred: {str(e)}"
        ))




















# from typing import Type
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, UploadFile, status

# from app.models.user_model import UserModel
# from app.dtos import user_dtos

# from app.libs import password_lib
# from app.utils import optional, error_parser

# from .get_by_user_email import get_user_by_email



# def user_login(db: Session, user: user_dtos.UserLoginPayloadDto) -> optional.Optional[Type[UserModel], Exception]:
#     # Validasi input user, jika email atau password kosong kembalikan 400 Bad Request
#     if not user.email or not user.password:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             error="Bad Request",
#             message="Email and password must be provided."
#         ))
    
#     # Cek apakah email yang diberikan ada di database
#     user_optional = get_user_by_email(db, user.email)
    
#     # Jika user tidak ditemukan (404 Not Found)
#     if user_optional.error:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             error="Not Found",
#             message="User with the provided email does not exist."
#         ))
#     user_model = user_optional.data  # Mengambil data user dari Optional
    
#     # Cek jika akun pengguna diblokir atau tidak aktif
#     if not user_model.is_active:  # Misalkan ada atribut is_active di model User
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             error="Forbidden",
#             message="Your account is not active. Please contact support."
#         ))

#     # Verifikasi password, jika tidak cocok kembalikan error 401
#     if not password_lib.verify_password(plain_password=user.password, hashed_password=user_model.hash_password):
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             error="UnAuthorized",
#             message="Password does not match."
#         ))

#     # Jika terjadi error selama generate token atau hal lain yang tidak terduga
#     try:
#         # Proses selanjutnya misalnya generate access token
#         return optional.build(data=user_model)

#     except Exception as e:
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message=f"An unexpected error occurred: {str(e)}"
#         ))

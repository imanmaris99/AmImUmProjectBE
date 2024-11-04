
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.dtos import user_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.jwt_lib import jwt_service
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
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Email and password must be provided."
                ).dict()
            )
        )

    try:
        # Autentikasi dengan Firebase
        firebase_user = authenticate_firebase_user(user.email, user.password)

        # Cek apakah pengguna ada di database lokal
        user_optional = get_user_by_email(db, user.email)
        
        if user_optional.error:
            # Jika user tidak ditemukan di database lokal, kembalikan error
            return optional.build(error=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message="User with the provided email does not exist."
                ).dict()
            ))
            
            # return optional.build(error=HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     error="Not Found",
            #     message="User with the provided email does not exist."
            # ))

        user_model = user_optional.data  # Mengambil data user dari Optional
        # Log untuk debugging role dan email
        print(f"User found: {user_model.email}, Role: {user_model.role}")

        # Cek apakah akun pengguna diblokir atau tidak aktif
        if not user_model.is_active:  # Misalkan ada atribut is_active di model User
            return optional.build(error=HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_403_FORBIDDEN,
                    error="Forbidden",
                    message="Your account is not active. Please contact support."
                ).dict()
            ))
            # return optional.build(error=HTTPException(
            #     status_code=status.HTTP_403_FORBIDDEN,
            #     error="Forbidden",
            #     message="Your account is not active. Please contact support."
            # ))

        # Verifikasi password (Firebase sudah memverifikasi password di langkah sebelumnya)
        if not password_lib.verify_password(plain_password=user.password, hashed_password=user_model.hash_password):
            return optional.build(error=HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error="Unauthorized",
                    message="Password does not match."
                ).dict()
            ))
            # return optional.build(error=HTTPException(
            #     status_code=status.HTTP_401_UNAUTHORIZED,
            #     error="Un Authorization",
            #     message="Password does not match."
            # ))

        # # Proses selanjutnya, misalnya generate JWT token
        # return optional.build(data=user_model)
                # Generate JWT token setelah autentikasi berhasil
        token_data = {
            "id": user_model.id,
            "role": user_model.role
        }
        access_token = jwt_service.create_access_token(token_data)
        print("Generated access token data:", token_data) 

        # Kembalikan token dan user info
        return optional.build(data={
            "access_token": access_token,
            "user": {
                "id": user_model.id,
                "email": user_model.email,
                "role": user_model.role,
                "is_active": user_model.is_active
            }
        })

    except SQLAlchemyError:
        return optional.build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An unexpected error occurred: {str(e)}"
            ).dict()
        ))
        # return optional.build(error=HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     error="Internal Server Error",
        #     message=f"An unexpected error occurred: {str(e)}"
        # ))




















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

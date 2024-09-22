from typing import Type
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile, status

from app.models.user_model import UserModel
from app.dtos import user_dtos

from app.libs import password_lib
from app.utils import optional, error_parser

from .get_by_user_email import get_user_by_email



def user_login(db: Session, user: user_dtos.UserLoginPayloadDto) -> optional.Optional[Type[UserModel], Exception]:
    # Cek apakah email yang diberikan ada di database
    user_optional = get_user_by_email(db, user.email)
    
    # Jika user tidak ditemukan (404 Not Found)
    if user_optional.error:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            error="Not Found",
            message="User with the provided email does not exist."
        ))
    user_model = user_optional.data  # Mengambil data user dari Optional
    
    # Verifikasi password, jika tidak cocok kembalikan error 401
    if not password_lib.verify_password(plain_password=user.password, hashed_password=user_model.hash_password):
        return optional.build(error=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="UnAuthorized",
            message="Password does not match."
        ))

    # Jika terjadi error selama generate token atau hal lain yang tidak terduga
    try:
        # Proses selanjutnya misalnya generate access token
        return optional.build(data=user_model)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message=f"An unexpected error occurred: {str(e)}"
        ))

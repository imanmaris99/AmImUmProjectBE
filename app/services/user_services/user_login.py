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
    
    # Jika ada error pada pencarian user, kembalikan error
    if user_optional.error:
        return user_optional

    user_model = user_optional.data  # Mengambil data user dari Optional
    
    # Verifikasi password, jika tidak cocok kembalikan error 401
    if not password_lib.verify_password(plain_password=user.password, hashed_password=user_model.hash_password):
        return optional.build(error=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password does not match."
        ))

    # Jika login berhasil, kembalikan data user
    return optional.build(data=user_model)

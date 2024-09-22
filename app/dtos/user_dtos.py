from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.libs.jwt_lib import jwt_dto 


class UserCreateDto(BaseModel):
    username: str = Field(default="username")
    email: EmailStr = Field(default="Example@Example.com")
    phone: str = Field(default="+6289965342543")
    password: str = Field(default="password")

class UserCreateResponseDto(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: str
    created_at: datetime
    updated_at: datetime

# class UserCreateResponseDto(BaseModel):
#     id: str
#     username: str
#     email: str
#     fullname: str
#     phone: Optional[str] = None
#     address: Optional[str] = None
#     photo_url: Optional[str] = None
#     about_me_list: list[str]
#     created_at: datetime
#     updated_at: datetime


class UserEditProfileDto(BaseModel):
    phone: str
    address: str
    about_me: str


class UserEditResponseDto(BaseModel):
    phone: str
    address: str
    about_me: str


class UserEditPhotoProfileDto(BaseModel):
    photo_url: str


class UserLoginPayloadDto(BaseModel):
    email: EmailStr = Field(default="Example@Example.com")
    password: str = Field(default="somePassword")

class UserLoginResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your user account has been login successfully")
    data: jwt_dto.AccessTokenDto  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur

# DTO untuk menangkap data dari JSON
class ChangePasswordDto(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponseDto(BaseModel):
    message : str = Field(default="Password has been changed successfully")
    data: ChangePasswordDto

class DeleteUserResponseDto(BaseModel):
    detail: str = Field(default="Your user account has been deleted successfully")
    user_id: str
    username: str
    email: str
    
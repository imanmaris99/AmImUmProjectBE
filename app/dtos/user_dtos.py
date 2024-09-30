from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.libs.jwt_lib import jwt_dto 


class UserCreateDto(BaseModel):
    firstname: str = Field(default="firstname")
    lastname: str = Field(default="lastname")
    gender: str = Field(default="man/woman")
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

class UserResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your user account has been create")
    data: UserCreateResponseDto  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur

class ResetPasswordDto(BaseModel):
    token: str
    new_password: str

class ForgotPasswordDto(BaseModel):
    email: EmailStr = Field(default="myemail@gmail.com")
    
class ForgotPasswordResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Password reset email has been sent.")
    data: ForgotPasswordDto

class ConfirmResetPasswordDto(BaseModel):
    email: EmailStr = Field(default="myemail@gmail.com")
    new_password: str = Field(default="Password@3")

class ConfirmResetPasswordResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your user account has been create")
    data: ConfirmResetPasswordDto  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur


class UserEditProfileDto(BaseModel):
    fullname: str
    address: str
    photo_url: str

class UserEditResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Edit profile has been success")
    data: UserEditProfileDto

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
    
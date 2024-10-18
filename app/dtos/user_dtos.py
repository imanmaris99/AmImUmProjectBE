from typing import Optional, Literal
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.libs.jwt_lib import jwt_dto 


class UserCreateDto(BaseModel):
    firstname: str = Field(default="firstname")
    lastname: str = Field(default="lastname")
    gender: Literal['man', 'woman'] = Field(default='man')
    email: EmailStr = Field(default="Example@Example.com")
    phone: str = Field(default="+6289965342543")
    password: str = Field(default="password")

class UserCreateResponseDto(BaseModel):
    id: str
    firebase_uid: Optional[str]
    firstname: Optional[str]
    lastname: Optional[str]
    gender: Optional[str]
    email: Optional[str]
    phone: Optional[str] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[str]
    is_active: bool 
    created_at: datetime
    updated_at: datetime

class UserResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your user account has been create")
    data: UserCreateResponseDto  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur

class ResetPasswordDto(BaseModel):
    oob_code: str
    email: EmailStr 
    new_password: str

class ResetPasswordResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Password reset email has been sent.")
    data: ResetPasswordDto

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
    firstname: str
    lastname: str
    phone: str
    address: str

class UserEditResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Edit profile has been success")
    data: UserEditProfileDto

class UserEditPhotoProfileDto(BaseModel):
    photo_url: str

class UserEditPhotoProfileResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Edit photo profile has been success")
    data: UserEditPhotoProfileDto

class UserLoginPayloadDto(BaseModel):
    email: EmailStr = Field(default="Example@Example.com")
    password: str = Field(default="somePassword")

class UserLoginResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your user account has been login successfully")
    data: dict  # atau Anda bisa spesifik jika user punya schema sendiri
    # data: jwt_dto.AccessTokenDto  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur

class GoogleLoginRequest(BaseModel):
    id_token: str

class GoogleLoginResponseRequestDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your user google account has been login successfully")
    data: UserCreateResponseDto


# DTO untuk menangkap data dari JSON
class ChangePasswordDto(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message : str = Field(default="Password has been changed successfully")
    data: ChangePasswordDto

class DeleteUserResponseDto(BaseModel):
    detail: str = Field(default="Your user account has been deleted successfully")
    user_id: str
    username: str
    email: str
    
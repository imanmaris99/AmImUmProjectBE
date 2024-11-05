from typing import Optional, Literal
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr, validator

import re

from app.libs.jwt_lib import jwt_dto 


# class UserCreateDto(BaseModel):
#     firstname: str = Field(default="firstname")
#     lastname: str = Field(default="lastname")
#     gender: Literal['male', 'female'] = Field(default='male')
#     email: EmailStr = Field(default="Example@Example.com")
#     phone: str = Field(default="+6289965342543")
#     password: str = Field(default="password")

class UserCreateDto(BaseModel):
    firstname: str = Field(..., description="First name of the user")
    lastname: str = Field(..., description="Last name of the user")
    gender: Literal['male', 'female'] = Field(..., description="Gender of the user")
    email: EmailStr = Field(..., description="Email address of the user")
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    password: str = Field(..., description="Password for the user account")

    @validator('phone')
    def validate_phone(cls, value):
        pattern = r"^\+62\d{10,11}$"
        if not re.match(pattern, value):
            raise ValueError("Phone number must start with +62 and contain 10-11 digits after that")
        return value
    
    # Fields with `...` (Ellipsis) will make the field required with no default values.
    # Validation will fail if any of these fields are missing or if the input is empty.

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

class EmailVerificationRequestDto(BaseModel):
    code: str = Field(..., description="verification code from email")
    email: EmailStr = Field(..., description="Email address of the user")

class EmailInfoVerificationRequestDto(BaseModel):
    code: str
    email: EmailStr 
    firstname: Optional[str]
    lastname: Optional[str]
    gender: Optional[str]
    role: Optional[str]
    is_active: bool 

class EmailVerificationResponseDto(BaseModel):
    status_code: int 
    message: str 
    data: EmailInfoVerificationRequestDto  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur


class ResetPasswordDto(BaseModel):
    email: EmailStr 
    code: str
    new_password: str

class ResetPasswordResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your password has been reset successfully")
    data: ResetPasswordDto

class ForgotPasswordDto(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user")
    
class ForgotPasswordResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Password reset email has been sent.")
    data: ForgotPasswordDto

class ConfirmResetPasswordDto(BaseModel):
    email: EmailStr = Field(..., description="Email address of the user")
    new_password: str = Field(..., description="Password for the user account")

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
    email: EmailStr = Field(..., description="Email address of the user")
    password: str = Field(..., description="Password of the user")

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
    
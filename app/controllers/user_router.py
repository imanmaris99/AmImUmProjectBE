from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_service, jwt_dto

from app.services import user_services
from app.dtos import user_dtos


router = APIRouter(
    prefix="/user",
    tags=["user"]
)

## == USER - REGISTER == ##
@router.post("/register", response_model=user_dtos.UserCreateResponseDto, status_code=status.HTTP_201_CREATED)
def create_user(user: user_dtos.UserCreateDto, db: Session = Depends(get_db)):
    """This method is used to create a user"""
    result = user_services.create_user(db, user)
    
    # Jika terdapat error, raise HTTPException
    if result.error:
        raise result.error

    # Mengembalikan data user yang berhasil dibuat dengan status 201 Created
    return result.unwrap()

## == USER - LOGIN == ##
@router.post("/login", response_model=jwt_dto.AccessTokenDto)
def user_login(user: user_dtos.UserLoginPayloadDto, db: Session = Depends(get_db)):
    """This method is used for user login"""
    
    # Memanggil service untuk login user
    user_optional = user_services.user_login(db=db, user=user)
    
    # Jika ada error, raise HTTPException dari user_optional
    if user_optional.error:
        raise user_optional.error
    
    # Generate access token berdasarkan user ID
    access_token = user_services.service_access_token(user_optional.data.id)
    
    # Return the generated access token
    return access_token
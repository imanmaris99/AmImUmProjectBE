from datetime import datetime, timedelta, timezone
import os
from typing import Annotated

import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status

from .jwt_dto import TokenPayLoad, AccessTokenDto

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('Secret_Key')
ALGORITHM = "HS256"

bare_token = HTTPBearer(description="")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> AccessTokenDto:
    to_encode = data.copy()
    expire = (datetime.now(timezone.utc) + expires_delta
              if expires_delta
              else datetime.now(timezone.utc) + timedelta(weeks=1))
    to_encode.update({"exp": expire})
    return AccessTokenDto(
        access_token=jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))


async def get_jwt_pyload(token: Annotated[HTTPAuthorizationCredentials, Depends(bare_token)]) -> TokenPayLoad:
    try:
        payload = jwt.decode(jwt=token.credentials, key=SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayLoad(id=payload.get("id"))
    
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials hallo",
            headers={"WWW-Authenticate": "Bearer"},
        )

def create_reset_password_token(email: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": email}  # "sub" biasanya diisi dengan identifier seperti email
    expire = (datetime.now(timezone.utc) + expires_delta
              if expires_delta
              else datetime.now(timezone.utc) + timedelta(minutes=30))  # Token kadaluarsa dalam 30 menit
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_reset_password_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")  # Mengambil email dari token
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request", 
                message="Invalid token.")
        return email
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            error="Bad Request",
            message="Token has expired.")
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            error="Bad Request",
            message="Invalid token.")

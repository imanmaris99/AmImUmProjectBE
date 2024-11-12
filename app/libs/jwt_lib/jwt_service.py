from datetime import datetime, timedelta, timezone
import os
from typing import Annotated

import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status

from .jwt_dto import TokenPayLoad, AccessTokenDto

from dotenv import load_dotenv

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Mengambil SECRET_KEY dari variabel lingkungan
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")

ALGORITHM = "HS256"
bearer_token = HTTPBearer(description="JWT token for authentication")

# Fungsi untuk membuat access token JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> AccessTokenDto:
    to_encode = data.copy()

    # Set expiration time
    expire = (datetime.now(timezone.utc) + expires_delta
              if expires_delta
              else datetime.now(timezone.utc) + timedelta(weeks=1))  # Default expiration 1 week    
   
    # Convert the expiration time to Unix timestamp
    exp_timestamp = int(expire.timestamp())
    exp_readable = expire.strftime("%Y-%m-%d %H:%M:%S")  # Convert to human-readable format
    
    to_encode.update({"exp": exp_timestamp})
    
    # Encode the JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Return the access token wrapped in a DTO
    return AccessTokenDto(access_token=encoded_jwt, exp=exp_readable)

# Fungsi untuk memvalidasi token JWT dan mengembalikan payload
async def get_jwt_pyload(token: Annotated[HTTPAuthorizationCredentials, Depends(bearer_token)]) -> TokenPayLoad:
    try:
        payload = jwt.decode(jwt=token.credentials, key=SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded JWT payload: {payload}")

        if "id" not in payload or "role" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "status_code":status.HTTP_401_UNAUTHORIZED,
                    "error":"Unauthorized",
                    "message":"Invalid token payload"
                },
                # error="Unauthorized",
                # message="Invalid token payload"
            )

        return TokenPayLoad(id=payload["id"], role=payload["role"])
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status_code":status.HTTP_401_UNAUTHORIZED,
                "error":"Unauthorized",
                "message":"Token has expired"
            },
            # error="UnAuthorized",
            # message="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
     
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status_code":status.HTTP_401_UNAUTHORIZED,
                "error":"Unauthorized",
                "message":"Could not validate credentials hallo"
            },
            # error="UnAuthorized",
            # message="Could not validate credentials hallo",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Fungsi untuk mendapatkan user dari token
def get_current_user(jwt_token: TokenPayLoad = Depends(get_jwt_pyload)):
    
    if not jwt_token :     
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
    )        
    return jwt_token


# Fungsi untuk memastikan user memiliki akses sebagai admin
def admin_access_required(jwt_token: TokenPayLoad = Depends(get_jwt_pyload)):
    print(f"Verifying access: User role - {jwt_token.role}") 
    if not jwt_token or jwt_token.role != "admin":     
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status_code": status.HTTP_403_FORBIDDEN,
                "error":"Forbidden",
                "message":"You do not have permission to access this resource."
            },
            # error="Forbidden",
            # message="You do not have permission to access this resource."
        )
    return jwt_token
    
# Fungsi untuk membuat token reset password
def create_reset_password_token(email: str, expires_delta: timedelta | None = None) -> str:
    to_encode = {"sub": email}  # "sub" biasanya digunakan untuk identifier seperti email
    
    # Set expiration time
    expire = (datetime.now(timezone.utc) + expires_delta
              if expires_delta
              else datetime.now(timezone.utc) + timedelta(minutes=30))  # Default expiration 30 minutes
    
    # Convert the expiration time to Unix timestamp
    to_encode.update({"exp": int(expire.timestamp())})
    
    # Encode the JWT
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Fungsi untuk memverifikasi token reset password
def verify_reset_password_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")  # Mengambil email dari token
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "error":"Bad Request",
                    "message":"Invalid token."
                },
                # error="Bad Request", 
                # message="Invalid token."
            )
        return email
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error":"Bad Request",
                "message":"Token has expired."
            },
            # error="Bad Request",
            # message="Token has expired."
        )
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail={
                "status_code": status.HTTP_400_BAD_REQUEST,
                "error":"Bad Request",
                "message":"Invalid token."
            },
            # error="Bad Request",
            # message="Invalid token."
        )




# Fungsi untuk membuat access token JWT
# def create_access_token(data: dict, expires_delta: timedelta | None = None) -> AccessTokenDto:
#     to_encode = data.copy()
#     expire = (datetime.now(timezone.utc) + expires_delta
#               if expires_delta
#               else datetime.now(timezone.utc) + timedelta(weeks=1))  # Default kadaluarsa 1 minggu
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return AccessTokenDto(access_token=encoded_jwt)


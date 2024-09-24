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

from typing import Optional
from pydantic import BaseModel, Field


class AccessTokenDto(BaseModel):
    # detail: str = Field(default="Your user account has been login successfully")
    access_token: str
    token_type: str = Field(default="bearer")
    exp: str

class TokenPayLoad(BaseModel):
    id: str
    role: Optional[str]  # Tambahkan atribut role

# class TokenPayLoad(BaseModel):
#     id: str

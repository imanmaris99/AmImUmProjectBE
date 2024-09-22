from pydantic import BaseModel, Field


class AccessTokenDto(BaseModel):
    # detail: str = Field(default="Your user account has been login successfully")
    access_token: str
    token_type: str = Field(default="bearer")

class TokenPayLoad(BaseModel):
    id: str

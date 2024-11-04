from pydantic import BaseModel

class ErrorResponseDto(BaseModel):
    status_code: int
    error: str
    message: str

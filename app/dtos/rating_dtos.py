from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RatingCreateDto(BaseModel):
    rate: Optional[int] = None
    review: Optional[str] = None

class RatingInfoCreateDto(BaseModel):
    id: int
    rate: Optional[int] = None
    review: Optional[str] = None
    product_name: Optional[str] = None
    rater_name: Optional[str] = None
    created_at: datetime

class RatingResponseCreateDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your rate for some product has been created")
    data: RatingInfoCreateDto

class RatingAllResponseDto(BaseModel):
    id: str
    rate: int
    review: Optional[str] = None
    product_name: Optional[str] = None
    rater_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ProductRatingDto(BaseModel):
    id: str
    rate: int
    review: str
    rater_name: Optional[str] = None


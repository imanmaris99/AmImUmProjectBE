from datetime import datetime
from pydantic import BaseModel, Field


class ProductImageInfoDto(BaseModel):
    id: int
    product_id: str
    url: str
    is_primary: bool
    sort_order: int
    mime_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None
    created_at: datetime


class ProductImageResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Product image uploaded")
    data: ProductImageInfoDto


class ProductImageOrderDto(BaseModel):
    image_ids: list[int]


class ProductImageActionResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="OK")

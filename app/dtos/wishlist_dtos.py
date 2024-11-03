from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime


class WishlistCreateOfIdProductDto(BaseModel):
    product_id: str

class WishlistInfoCreateDto(BaseModel):
    id: int
    product_name: Optional[str] = None
    product_variant: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

class WishlistResponseCreateDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your wishlist for the product has been saved")
    data: WishlistInfoCreateDto


class AllWishlistResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your all of products wishlist success to access")
    total_records: int = Field(default=3)
    data: List[WishlistInfoCreateDto]

class DeleteByIdWishlistDto(BaseModel):
    wishlist_id: int

class InfoDeleteWishlistDto(BaseModel):
    wishlist_id: int = Field(default=2)
    product_name: str= Field(default="buyung upik")

class DeleteWishlistResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your product wishlist has been deleted")
    data: InfoDeleteWishlistDto
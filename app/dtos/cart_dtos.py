from pydantic import BaseModel, Field, conint
from typing import Any, Dict, Optional, List
from datetime import datetime


class CartCreateOfIdProductDto(BaseModel):
    product_id: str  # UUID as CHAR(36)
    variant_id: int

class CartInfoCreateDto(BaseModel):
    id: int
    product_name: Optional[str] = None
    variant_product: Optional[str] = None
    quantity: int
    is_active: bool
    customer_name: str
    created_at: datetime

class CartResponseCreateDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your wishlist for the product has been saved")
    data: CartInfoCreateDto

class AllCartResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your all of products wishlist success to access")
    total_records: int = Field(default=3)
    data: List[CartInfoCreateDto]
    all_item_active_prices: float
    all_promo_active_prices: float
    total_all_active_prices: float
    

class UpdateByIdCartDto(BaseModel):
    cart_id: int

class UpdateQuantityItemDto(BaseModel):
    quantity: Optional[conint(gt=0)] 

class UpdateActivateItemDto(BaseModel):
    is_active: bool 


class DeleteByIdCartDto(BaseModel):
    cart_id: int

class InfoDeleteCartDto(BaseModel):
    cart_id: int = Field(default=2)
    product_name: str= Field(default="buyung upik")
    variant_product: str= Field(default="cokelat")

class DeleteCartResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="One of All list your product item in cart has been deleted")
    data: InfoDeleteCartDto
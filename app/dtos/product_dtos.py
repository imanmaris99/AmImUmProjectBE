from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.dtos.rating_dtos import ProductRatingDto
from app.dtos.pack_type_dtos import VariantProductDto

class ProductCreateDTO(BaseModel):
    name: str
    info: Optional[str]
    pack_type_id: int
    description: Optional[str]
    instructions: Optional[str]
    price: float
    product_by_id: int

class ProductInfoDTO(BaseModel):
    id: int
    name: str
    info: Optional[str]
    pack_type_id: int
    description: Optional[str]
    instructions: Optional[str]
    price: float
    is_active: bool
    product_by_id: int
    created_at: datetime
    updated_at: datetime

class ProductResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your product has been create")
    data: ProductInfoDTO  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur

class ProductUpdateDTO(BaseModel):
    name: Optional[str]
    info: Optional[str]
    pack_type_id: Optional[int]
    description: Optional[str]
    instructions: Optional[str]
    price: Optional[float]
    is_active: Optional[bool]
    product_by_id: Optional[int]


class ProductDetailResponseDTO(BaseModel):
    id: int
    name: str
    info: Optional[str]
    variants_list: List[VariantProductDto]
    description: Optional[str]
    instructions: Optional[str]
    price: float
    is_active: bool
    company: str
    avg_rating: Optional[float] = None
    total_rater: Optional[int] = None
    rating_list: List[ProductRatingDto]
    created_at: datetime
    updated_at: datetime


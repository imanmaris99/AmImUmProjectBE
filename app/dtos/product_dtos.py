from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.dtos.rating_dtos import ProductRatingDto
from app.dtos.pack_type_dtos import VariantProductDto, VariantAllProductDto

class ProductCreateDTO(BaseModel):
    name: str= Field(default="buyung upik")
    info: Optional[str] = Field(default="1pack isi 11sachet dengan berat ± 5gram")
    weight: int= Field(default=50)
    description: Optional[str]= Field(default="some descriptions")
    instruction: Optional[str]= Field(default="some instructions")
    price: float= Field(default=8000.0)
    product_by_id: int= Field(default=3)

class ProductInfoDTO(BaseModel):
    id: str
    name: str= Field(default="buyung upik")
    info: Optional[str] = Field(default="1pack isi 11sachet dengan berat ± 5gram")
    weight: int= Field(default=50)
    description: str= Field(default="some descriptions")
    instruction: str= Field(default="some instructions")
    price: float= Field(default=8000.0)
    product_by_id: int= Field(default=3)
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ProductResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your product has been create")
    data: ProductInfoDTO  # Atau Anda bisa membuat model terpisah untuk data yang lebih terstruktur

class AllProductInfoDTO(BaseModel):
    id: Optional[str]
    name: Optional[str]= Field(default="buyung upik")
    price: float= Field(default=8000.0)
    all_variants: List[VariantAllProductDto]
    created_at: datetime

class ProductListScrollResponseDto(BaseModel):
    data: List[AllProductInfoDTO]
    has_more: bool  # Indikasi apakah masih ada data lain

class ProductIdToUpdateDTO(BaseModel):
    product_id: str = Field(default="287ba5f9-c495-455d-9e38-8ceb3cac61ba")

class ProductUpdateDTO(BaseModel):
    name: Optional[str]
    info: Optional[str]
    weight: Optional[int]
    description: Optional[str]
    instructions: Optional[str]
    price: Optional[float]


class ProductDetailDTO(BaseModel):
    id: str
    name: str
    info: Optional[str]
    variants_list: List[VariantProductDto]
    description_list: List[str]
    instructions_list: List[str]
    price: float
    is_active: bool
    company: str
    avg_rating: Optional[float] = None
    total_rater: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class ProductDetailResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Product details successfully retrieved")
    data: ProductDetailDTO 

class ProductInfoByIdProductionDTO(BaseModel):
    production_id: int

class DeleteByIdProductDto(BaseModel):
    product_id: str = Field(default="287ba5f9-c495-455d-9e38-8ceb3cac61ba")

class InfoDeleteProductDto(BaseModel):
    product_id: str = Field(default="287ba5f9-c495-455d-9e38-8ceb3cac61ba")
    name: str= Field(default="buyung upik")

class DeleteProductResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your product has been deleted")
    data: InfoDeleteProductDto
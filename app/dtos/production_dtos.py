from pydantic import BaseModel, Field
from typing import Optional, List

class ProductionCreateDto(BaseModel):
    name: str
    herbal_category_id: int = Field(default=1)
    description: Optional[str] = None

class PostLogoCompanyDto(BaseModel):
    photo_url: str

class PostLogoCompanyResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Post your Company-Logo has been success")
    data: PostLogoCompanyDto

class ProductionCreateWithPhotoDto(BaseModel):
    name: str
    herbal_category_id: int = Field(default=1)
    description: Optional[str] = None
    photo_url: Optional[str] = None

class ProductionCreateResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Create manufactured by some Company has been success")
    data: ProductionCreateDto

class AllProductionsDto(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    description_list: list[str]
    category: Optional[str] = None
    created_at: str

class AllProductionPromoDto(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    promo_special: Optional[float] = None
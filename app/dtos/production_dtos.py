from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class ProductionCreateDto(BaseModel):
    name: str
    herbal_category_id: int = Field(default=1)
    description: Optional[str] = None

class ProductionIdToUpdateDto(BaseModel):
    production_id:int

# DTO untuk memperbarui informasi artikel
class ProductionInfoUpdateDTO(BaseModel):
    name: Optional[str]
    description: Optional[str] = None

class ProductionInfoUpdateResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Updated Info about some company production has been success")
    data: ProductionInfoUpdateDTO   

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
    created_at: datetime

class AllListProductionResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All list products from Production or brand successfully retrieved")
    data: List[AllProductionsDto]

class ArticleListScrollResponseDto(BaseModel):
    data: List[AllProductionsDto]
    remaining_records: int
    has_more: bool  # Indikasi apakah masih ada data lain

class DetailProductionDto(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    description_list: list[str]
    category: Optional[str] = None
    total_product: Optional[int] = None
    created_at: datetime

class ProductionDetailResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Info about Production or brand details successfully retrieved")
    data: DetailProductionDto

class AllProductionPromoDto(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    promo_special: Optional[float] = None

class AllProductionPromoResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Info about promo from Production or brand successfully retrieved")
    data: List[AllProductionPromoDto]

class InfoDeleteProductionDto(BaseModel):
    id: int
    name: str

class DeleteProdutionResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Info about company some product has been deleted")
    data: InfoDeleteProductionDto


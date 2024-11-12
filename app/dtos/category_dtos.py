from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, validator, field_validator, Field


class CategoryCreateDto(BaseModel):
    name: str = Field(default="Jamu Produksi Pabrik")
    description: str = Field(default="menggunakan teknologi yang modern sehingga dapat diproduksi dalam jumlah yang besar dengan kualitas yang baik.")

class CategoryCreateResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Create tag categories has been success")
    data: CategoryCreateDto

class AllCategoryResponseDto(BaseModel):
    id: int
    name: str
    description_list: list[str]
    created_at: datetime
class AllCategoryInfoResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="All list of tag categories has been success access")
    data: List[AllCategoryResponseDto]
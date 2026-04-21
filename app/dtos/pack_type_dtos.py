from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PackTypeCreateDto(BaseModel):
    product_id: str
    name: str
    min_amount: int = Field(..., ge=1)
    variant: Optional[str] = None
    expiration: Optional[str] = None
    stock: int = Field(..., ge=0)
    price: float = Field(..., ge=0)
    discount: Optional[float] = Field(default=None, ge=0, le=100)

    @field_validator("product_id", "name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("variant", "expiration")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PackTypeInfoDto(BaseModel):
    id: int
    img: Optional[str] = None
    product_id: str
    product: Optional[str] = None
    name: str
    min_amount: int
    variant: Optional[str] = None
    expiration: Optional[str] = None
    stock: int
    price: float
    discount: Optional[float] = None
    discounted_price: float
    fk_admin_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PackTypeResponseCreateDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your pack and variant type product has been created")
    data: PackTypeInfoDto


class TypeIdToUpdateDto(BaseModel):
    type_id: int


class PackTypeEditInfoDto(BaseModel):
    stock: Optional[int] = Field(default=None, ge=0)
    price: Optional[float] = Field(default=None, ge=0)
    discount: Optional[float] = Field(default=None, ge=0, le=100)
    variant: Optional[str] = None
    expiration: Optional[str] = None

    @field_validator("variant", "expiration")
    @classmethod
    def normalize_update_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PackTypeUpdatedInfoDto(BaseModel):
    id: int
    product_id: str
    product: Optional[str] = None
    name: str
    img: Optional[str] = None
    variant: Optional[str] = None
    expiration: Optional[str] = None
    stock: int
    price: float
    discount: Optional[float] = None
    discounted_price: float
    updated_at: datetime


class EditPhotoProductDto(BaseModel):
    img: str


class EditPhotoProductResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Edit photo product has been success")
    data: EditPhotoProductDto


class VariantProductDto(BaseModel):
    id: int
    product: str
    name: str
    img: Optional[str] = None
    variant: Optional[str] = None
    expiration: Optional[str] = None
    stock: int
    price: float
    discount: Optional[float] = None
    discounted_price: float
    updated_at: datetime


class PackTypeEditInfoResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Edit stock and discount product has been success")
    data: PackTypeUpdatedInfoDto


class VariantAllProductDto(BaseModel):
    id: Optional[int] = None
    product_id: Optional[str] = None
    product: Optional[str] = None
    name: Optional[str] = None
    variant: Optional[str] = None
    img: Optional[str] = None
    expiration: Optional[str] = None
    stock: Optional[int] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    discounted_price: Optional[float] = None
    updated_at: datetime


class AllVariantsProductInfoResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="All variants from all products has been create")
    data: List[VariantAllProductDto]


class DeletePackTypeDto(BaseModel):
    type_id: int


class InfoDeletePackTypeDto(BaseModel):
    type_id: int
    variant: str


class DeletePackTypeResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your pack and variant type product has been deleted")
    data: InfoDeletePackTypeDto


class VariantProductCartDto(BaseModel):
    id: int
    variant: Optional[str] = None
    name: str
    img: Optional[str] = None
    price: float
    discount: Optional[float] = None
    discounted_price: float

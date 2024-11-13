from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PackTypeCreateDto(BaseModel):
    product_id: str = Field(default="5e4da772-e77b-4889-8314-7b9930a13c71")
    name: str = Field(default="gram/ dosh/ botol")
    min_amount: int = Field(default="1")
    variant: Optional[str]= Field(default="Cokelat")
    expiration: Optional[str] = Field(default="12/25/2025")
    stock: int= Field(default="100")


class PackTypeInfoDto(BaseModel):
    id: int
    img: Optional[str] = None
    product_id: str = Field(default="5e4da772-e77b-4889-8314-7b9930a13c71")
    name: str = Field(default="gram/ dosh/ botol")
    min_amount: int = Field(default="1")
    variant: Optional[str]= Field(default="Cokelat")
    expiration: Optional[str] = Field(default="12 Desember 2024")
    stock: int= Field(default="100")
    discount: Optional[float] = None
    fk_admin_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class PackTypeResponseCreateDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your pack and variant type product has been created")
    data: PackTypeInfoDto

class TypeIdToUpdateDto(BaseModel):
    type_id:int

class PackTypeEditInfoDto(BaseModel):
    stock: int = Field(default=100)  # Nilai default diatur ke 100
    discount: Optional[float] = Field(default=30.0)  # Nilai default diatur ke 30.0, bukan 30%

class EditPhotoProductDto(BaseModel):
    img: str

class EditPhotoProductResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Edit photo product has been success")
    data: EditPhotoProductDto

class VariantProductDto(BaseModel):
    id: int
    product:str
    name: str
    img: Optional[str] = None
    variant: Optional[str]
    expiration: Optional[str]
    stock: int
    discount: Optional[float] = None
    discounted_price: Optional[float] = None
    updated_at: datetime


class PackTypeEditInfoResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Edit stock and discount product has been success")
    data: VariantProductDto

class VariantAllProductDto(BaseModel):
    id: Optional[int] = None
    variant: Optional[str] = None
    img: Optional[str] = None
    discount: Optional[float] = None
    discounted_price: Optional[float] = None
    updated_at: datetime
class AllVariantsProductInfoResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="All variants from all products has been create")
    data: List[VariantAllProductDto]

class DeletePackTypeDto(BaseModel):
    type_id:int
class InfoDeletePackTypeDto(BaseModel):
    type_id: int
    variant: str
class DeletePackTypeResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your pack and variant type product has been deleted")
    data: InfoDeletePackTypeDto


class VariantProductCartDto(BaseModel):
    id: int
    variant: Optional[str]
    name: str
    img: Optional[str] = None
    discount: Optional[float] = None

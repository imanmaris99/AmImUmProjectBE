from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProductCreateDTO(BaseModel):
    name: str
    info: Optional[str]
    pack_type_id: int
    description: Optional[str]
    instructions: Optional[str]
    price: float
    is_active: bool = True
    product_by_id: int

class ProductUpdateDTO(BaseModel):
    name: Optional[str]
    info: Optional[str]
    pack_type_id: Optional[int]
    description: Optional[str]
    instructions: Optional[str]
    price: Optional[float]
    is_active: Optional[bool]
    product_by_id: Optional[int]

class ProductResponseDTO(BaseModel):
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

    # class Config:
    #     orm_mode = True

    class Config:
        from_attributes = True  # Ubah dari orm_mode ke from_attributes

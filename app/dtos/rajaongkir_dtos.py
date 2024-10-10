from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# DTO untuk Province
class ProvinceDto(BaseModel):
    province_id: int
    province: str

class CityDto(BaseModel):
    city_id: int
    province_id: int
    province: str
    type: str
    city_name: str
    postal_code: int

# DTO untuk request biaya kirim
class ShippingCostRequest(BaseModel):
    origin: int = Field(default=497, description="ID kota atau kabupaten asal")
    destination: int = Field(default=455, description="ID kota atau kabupaten tujuan")
    weight: int = Field(default=1000, description="Berat dalam gram")
    courier: Literal['jne', 'pos', 'tiki'] = Field(default='jne')

# DTO untuk detail biaya pengiriman
class ShippingCostDetailDto(BaseModel):
    service: str
    description: str
    cost: int
    etd: str

# DTO untuk Shipping Cost
class ShippingCostDto(BaseModel):
    courier: str
    details: List[ShippingCostDetailDto]

# DTO untuk Province ID
class ProvinceIdDto(BaseModel):
    province_id: Optional[int] = None



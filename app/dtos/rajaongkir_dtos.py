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
    origin: int = Field(..., description="ID kota atau kabupaten asal")
    destination: int = Field(..., description="ID kota atau kabupaten tujuan")
    weight: int = Field(..., description="Berat dalam gram")
    courier: Literal['jne', 'pos', 'tiki'] = Field(..., description="Kurir jasa Kirim")

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



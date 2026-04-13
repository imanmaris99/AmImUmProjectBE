from pydantic import BaseModel, Field
from typing import List, Literal, Optional

SUPPORTED_DOMESTIC_COURIERS = (
    'jne', 'sicepat', 'ide', 'sap', 'jnt', 'ninja', 'tiki', 'lion',
    'anteraja', 'pos', 'ncs', 'rex', 'rpx', 'sentral', 'star', 'wahana', 'dse'
)

# DTO untuk Province
class ProvinceDto(BaseModel):
    province_id: int
    province: str

class AllProvincesResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Data Provinces from Database success to access")
    data: List[ProvinceDto]

class CityDto(BaseModel):
    city_id: int
    province_id: int = 0
    province: str = ""
    type: str = "city"
    city_name: str
    postal_code: int = 0

class AllCitiesResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Data Cities from Database success to access")
    data: List[CityDto]

class DistrictDto(BaseModel):
    district_id: int
    district: str

class AllDistrictsResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Data Districts from Database success to access")
    data: List[DistrictDto]


class ShippingCostRequest(BaseModel):
    origin: int = Field(..., description="ID origin domestic destination dari Komerce/RajaOngkir")
    destination: int = Field(..., description="ID destination domestic destination dari Komerce/RajaOngkir")
    weight: int = Field(..., description="Berat dalam gram")
    courier: Literal[*SUPPORTED_DOMESTIC_COURIERS] = Field(..., description="Kode kurir domestic yang didukung Komerce/RajaOngkir")

# DTO untuk detail biaya pengiriman
class ShippingCostDetailDto(BaseModel):
    service: str
    description: str
    cost: int
    etd: str

class AllShippingCostResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Data shipping cost from Database success to access")
    data: List[ShippingCostDetailDto]

# DTO untuk Shipping Cost
class ShippingCostDto(BaseModel):
    courier: str
    details: List[ShippingCostDetailDto]

# DTO untuk Province ID
class ProvinceIdDto(BaseModel):
    province_id: Optional[int] = None



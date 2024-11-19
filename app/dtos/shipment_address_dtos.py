from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal

import re

class ShipmentAddressIdToUpdateDto(BaseModel):
    address_id:int

class ShipmentAddressCreateDto(BaseModel):
    name: str
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    address: Optional[str] = None
    city: Optional[str] = None
    city_id: Optional[int] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[int] = None

    @validator('phone')
    def validate_phone(cls, value):
        pattern = r"^\+62\d{10,11}$"
        if not re.match(pattern, value):
            raise ValueError("Phone number must start with +62 and contain 10-11 digits after that")
        return value
    
class ShipmentAddressInfoDto(BaseModel):
    id: int
    name: str
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    address: Optional[str] = None
    city: Optional[str] = None
    city_id: Optional[int] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[int] = None
    created_at: datetime

class ShipmentAddressResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your shipping address input has been saved")
    data: ShipmentAddressInfoDto

class AllAddressListResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Data courier shipping in your account success to access")
    data: List[ShipmentAddressInfoDto]

class MyShipmentAddressInfoDto(BaseModel):
    id: int
    name: str
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    address: Optional[str] = None
    created_at: datetime

class DeleteAddressDto(BaseModel):
    address_id:int

class DeleteAddressInfoDto(BaseModel):
    address_id:int
    name: str
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    address: Optional[str] = None

class DeleteAddressResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your courier choice has been deleted")
    data: DeleteAddressInfoDto


class DataShipmentAddressInfoDto(BaseModel):
    id: int
    name: str
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[int] = None
    created_at: datetime
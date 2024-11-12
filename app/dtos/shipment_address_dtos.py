from datetime import datetime
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal

import re


class ShipmentAddressCreateDto(BaseModel):
    name: str
    phone: str = Field(..., description="Phone number of the user, must start with +62 and contain 10-11 digits after that")
    address: Optional[str] = None
    city: Optional[str] = None
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
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[int] = None
    created_at: datetime

class ShipmentAddressResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your shipping address input has been saved")
    data: ShipmentAddressInfoDto

# class CourierIdToUpdateDto(BaseModel):
#     courier_id:int

# class CourierDataWeightUpdateDTO(BaseModel):
#     courier_name: Literal['jne', 'pos', 'tiki'] = Field(..., description="Kurir jasa Kirim") 
#     weight: int

# class CourierInfoUpdateWeightResponseDto(BaseModel):
#     status_code: int = Field(default=200)
#     message: str = Field(default="updated data weight and courier of shipping successfully")
#     data: CourierDataWeightUpdateDTO

# class CourierDataUpdateDTO(BaseModel):
#     service_type: str
#     cost: Optional[float] = None

# class CourierInfoUpdateResponseDto(BaseModel):
#     status_code: int = Field(default=200)
#     message: str = Field(default="updated data of courier successfully")
#     data: CourierDataUpdateDTO

# class AllCourierListResponseCreateDto(BaseModel):
#     status_code: int = Field(default=200)
#     message: str = Field(default="All Data courier shipping in your account success to access")
#     data: List[CourierInfoDto]

# class DeleteCourierDto(BaseModel):
#     courier_id:int

# class DeleteInfoCourierDto(BaseModel):
#     courier_id: int
#     courier_name: str
#     service_type: str
#     cost: Optional[float] = None

# class DeleteCourierResponseDto(BaseModel):
#     status_code: int = Field(default=200)
#     message: str = Field(default="Your courier choice has been deleted")
#     data: DeleteInfoCourierDto
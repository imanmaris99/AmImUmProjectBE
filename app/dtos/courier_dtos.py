from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class CourierCreateDto(BaseModel):
    courier_name: Literal['jne', 'pos', 'tiki'] = Field(..., description="Kurir jasa Kirim") 
    weight: Optional[int] 
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    service_type: Optional[str] = None
    cost: Optional[float] = None
    estimated_delivery: Optional[str] = None
    
class CourierInfoDto(BaseModel):
    id: int
    courier_name: str
    weight: int
    phone_number: Optional[str] = None
    service_type: Optional[str] = None
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    cost: Optional[float] = None
    estimated_delivery: Optional[str] = None
    is_active: bool
    created_at: datetime

class CourierResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your courier shipping input has been saved")
    data: CourierInfoDto

class MyCourierInfoDto(BaseModel):
    id: int
    courier_name: str
    weight: int
    service_type: Optional[str] = None
    cost: Optional[float] = None
    estimated_delivery: Optional[str] = None
    created_at: datetime

class CourierIdToUpdateDto(BaseModel):
    courier_id:int

class CourierDataWeightUpdateDTO(BaseModel):
    courier_name: Literal['jne', 'pos', 'tiki'] = Field(..., description="Kurir jasa Kirim") 
    weight: int

class CourierInfoUpdateWeightResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="updated data weight and courier of shipping successfully")
    data: CourierDataWeightUpdateDTO

class CourierDataUpdateDTO(BaseModel):
    service_type: str
    cost: Optional[float] = None

class CourierInfoUpdateResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="updated data of courier successfully")
    data: CourierDataUpdateDTO

class AllCourierListResponseCreateDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Data courier shipping in your account success to access")
    data: List[CourierInfoDto]

class DeleteCourierDto(BaseModel):
    courier_id:int

class DeleteInfoCourierDto(BaseModel):
    courier_id: int
    courier_name: str
    service_type: str
    cost: Optional[float] = None

class DeleteCourierResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your courier choice has been deleted")
    data: DeleteInfoCourierDto

class DataCourierInfoDto(BaseModel):
    id: int
    courier_name: str
    weight: int
    service_type: Optional[str] = None
    cost: Optional[float] = None
    estimated_delivery: Optional[str] = None
    is_active: bool
    created_at: datetime
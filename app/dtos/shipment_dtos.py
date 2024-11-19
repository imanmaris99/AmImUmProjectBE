from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from app.dtos.shipment_address_dtos import ShipmentAddressCreateDto, MyShipmentAddressInfoDto, DataShipmentAddressInfoDto
from app.dtos.courier_dtos import CourierCreateDto, MyCourierInfoDto, DataCourierInfoDto

class ShipmentIdToUpdateDto(BaseModel):
    shipment_id:str

class RequestIdToUpdateDto(BaseModel):
    address_id: int
    courier_id: int

class ShipmentCreateDto(BaseModel):
    address: ShipmentAddressCreateDto
    courier: CourierCreateDto
    # code_tracking: str = Field(..., description="Kode pelacakan pengiriman")

class ShipmentInfoDto(BaseModel):
    shipment_id: str
    courier_id: int
    address_id: int
    code_tracking: str
    created_at: datetime
    is_active: bool

class UpdateActivateDto(BaseModel):
    is_active: bool 

class ShipmentResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Shipment has been successfully created")
    data: ShipmentInfoDto

class ShipmentActivateResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Shipment activation has been successfully updated")
    data: ShipmentInfoDto

class MyShipmentInfoDto(BaseModel):
    id: str
    my_address: MyShipmentAddressInfoDto
    my_courier: MyCourierInfoDto
    is_active: bool
    created_at: datetime

class MyListShipmentResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All list of info Shipment has been successfully access")
    data: List[MyShipmentInfoDto]

class MyShipmentUpdateResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Info Shipment has been successfully updated")
    data: MyShipmentInfoDto

class ShipmentDetailInfoListDto(BaseModel):
    shipment_id: str
    courier_info: DataCourierInfoDto
    address_info: DataShipmentAddressInfoDto
    code_tracking: str
    created_at: datetime

class AllShipmentListResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="All Info about Shipment has been successfully access")
    data: List[ShipmentDetailInfoListDto]


class DeleteShipmentInfoDto(BaseModel):
    id: str
    my_address: MyShipmentAddressInfoDto
    my_courier: MyCourierInfoDto
    created_at: datetime

class DeleteShipmentInfoResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="One of all list shipment in your account has been deleted")
    data: DeleteShipmentInfoDto
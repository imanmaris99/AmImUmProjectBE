from datetime import datetime
from pydantic import BaseModel, Field
from app.dtos.shipment_address_dtos import ShipmentAddressCreateDto
from app.dtos.courier_dtos import CourierCreateDto

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

class ShipmentResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Shipment has been successfully created")
    data: ShipmentInfoDto

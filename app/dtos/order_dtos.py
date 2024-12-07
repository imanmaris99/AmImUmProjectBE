from pydantic import BaseModel, Field, root_validator
from typing import List, Optional
from datetime import datetime

from app.dtos.order_item_dtos import OrderItemDto
from app.dtos.shipment_dtos import MyShipmentAddressOrderInfoDto
from app.models.enums import DeliveryTypeEnum


class OrderIdCompleteDataDTO(BaseModel):
    order_id: str

class OrderCreateDTO(BaseModel):
    delivery_type: DeliveryTypeEnum
    notes: Optional[str] = None
    shipment_id: Optional[str] = None

    @root_validator(skip_on_failure=True)
    def validate_pickup_notes(cls, values):
        delivery_type = values.get("delivery_type")
        notes = values.get("notes")
        
        if delivery_type == DeliveryTypeEnum.pickup and not notes:
            raise ValueError("Notes wajib diisi untuk pengiriman tipe pickup.")
        return values
    
class OrderCreateInfoDTO(BaseModel):
    id: str
    status: str
    total_price: float
    shipment_id: Optional[int] = None
    delivery_type: DeliveryTypeEnum
    notes: Optional[str] = None
    created_at: datetime

class OrderInfoResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your order has been saved")
    data: OrderCreateInfoDTO

class GetOrderInfoDto(BaseModel):
    id: str
    status: str
    total_price: Optional[float] = 0.0
    shipment_id: Optional[str] = None
    delivery_type: DeliveryTypeEnum
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    created_at: datetime
    shipping_cost: Optional[float] = 0.0
    order_item_lists: List[OrderItemDto]

class GetOrderInfoResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Information about your order successfully retrieved")
    data: List[GetOrderInfoDto]

class GetOrderDetailDto(BaseModel):
    id: str
    status: str
    total_price: Optional[float] = 0.0
    delivery_type: str
    notes: Optional[str]
    customer_name: str
    created_at: datetime
    shipping_cost: Optional[float] = 0.0
    my_shipping: Optional[MyShipmentAddressOrderInfoDto]
    order_item_lists: List[OrderItemDto]

class GetOrderDetailResponseDto(BaseModel):
    status_code: int
    message: str
    data: GetOrderDetailDto
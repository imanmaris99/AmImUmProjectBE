from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from app.dtos.order_item_dtos import OrderItemDto
from app.dtos.shipment_dtos import MyShipmentAddressOrderInfoDto
from app.models.enums import DeliveryTypeEnum


class OrderIdCompleteDataDTO(BaseModel):
    order_id: str

class OrderCreateDTO(BaseModel):
    delivery_type: DeliveryTypeEnum
    notes: Optional[str] = None
    shipment_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_pickup_notes(self):
        if self.delivery_type == DeliveryTypeEnum.pickup and not self.notes:
            raise ValueError("Notes wajib diisi untuk pengiriman tipe pickup.")
        return self
    
class OrderCreateInfoDTO(BaseModel):
    id: str
    status: str
    total_price: float
    shipment_id: Optional[str] = None
    delivery_type: DeliveryTypeEnum
    notes: Optional[str] = None
    created_at: datetime

class OrderInfoResponseDataDto(BaseModel):
    id: str
    status: str
    total_price: float
    shipment_id: Optional[str] = None
    delivery_type: DeliveryTypeEnum
    notes: Optional[str] = None
    created_at: datetime

class OrderInfoResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your order has been saved")
    data: OrderInfoResponseDataDto

class AdminOrderStatusUpdateDto(BaseModel):
    status: str

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

class PaginationMetaDto(BaseModel):
    skip: int = 0
    limit: int = 100
    count: int = 0

class GetOrderInfoResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Information about your order successfully retrieved")
    data: List[GetOrderInfoDto]
    meta: Optional[PaginationMetaDto] = None

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
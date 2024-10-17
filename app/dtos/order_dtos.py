from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class OrderItemDTO(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderCreateDTO(BaseModel):
    customer_id: Optional[int]  # Nullable for non-member
    payment_type: str
    shipment_id: Optional[int]
    order_items: List[OrderItemDTO]

class OrderResponseDTO(BaseModel):
    id: int
    status: str
    total_price: float
    customer_id: Optional[int]
    payment_type: str
    shipment_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemDTO]

    # class Config:
    #     orm_mode = True

    class Config:
        from_attributes = True  # Ubah dari orm_mode ke from_attributes
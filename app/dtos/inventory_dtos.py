from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


MovementType = Literal["in", "out", "adjust", "sale", "return", "snapshot"]


class StockMovementItemDto(BaseModel):
    id: str
    variant_id: int
    product_id: Optional[str] = None
    movement_type: MovementType
    delta: int
    stock_before: Optional[int] = None
    stock_after: Optional[int] = None
    actor_id: Optional[str] = None
    reason: Optional[str] = None
    reference: Optional[str] = None
    created_at: datetime


class StockMovementListDataDto(BaseModel):
    items: List[StockMovementItemDto]
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1)
    total: int = Field(default=0, ge=0)


class StockMovementListResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Success")
    data: StockMovementListDataDto


class StockAdjustmentRequestDto(BaseModel):
    variant_id: int
    delta: int
    reason: str
    reference: Optional[str] = None


class StockAdjustmentResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Stock adjusted successfully")
    data: StockMovementItemDto


class InventoryThresholdRequestDto(BaseModel):
    min_threshold: int = Field(ge=0)


class InventoryThresholdDto(BaseModel):
    variant_id: int
    min_threshold: int
    updated_by: Optional[str] = None
    updated_at: datetime


class InventoryThresholdResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Inventory threshold updated successfully")
    data: InventoryThresholdDto

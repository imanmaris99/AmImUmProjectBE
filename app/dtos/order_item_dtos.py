from pydantic import BaseModel, Field, root_validator
from typing import Any, Dict, Optional, List
from datetime import datetime

class OrderItemDto(BaseModel):
    id: int
    product_name: Optional[str] = None
    variant_product: Optional[str] = None
    variant_discount: Optional[float] = 0.0  # Jadikan opsional dengan default 0.0
    quantity: Optional[int] = None
    price_per_item: Optional[float] = 0.0
    total_price: Optional[float] = 0.0
    created_at: datetime
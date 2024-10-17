from pydantic import BaseModel
from typing import Optional, Any

class PaymentRequestDTO(BaseModel):
    order_id: int
    payment_type: str  # Contoh: 'credit_card', 'bank_transfer'
    gross_amount: float

class PaymentResponseDTO(BaseModel):
    transaction_id: Optional[str]
    redirect_url: Optional[str]
    token: Optional[str]
    transaction_status: Optional[str]
    status_code: int
    message: Optional[str]

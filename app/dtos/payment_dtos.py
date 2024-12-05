from pydantic import BaseModel, Field, validator
from typing import Optional, Any
from app.models.enums import PaymentTypeEnum, TransactionStatusEnum, FraudStatusEnum  # Mengimpor Enum

class PaymentOrderByIdDto(BaseModel):
    order_id: str  # UUID dari order yang akan dibayar

class PaymentCreateDto(BaseModel):
    order_id: str  # UUID dari order yang akan dibayar
    payment_type: str  # Jenis pembayaran (credit_card, gopay, bank_transfer, dll.)

    @validator("payment_type")
    def validate_payment_type(cls, value):
        # Mengambil metode pembayaran yang valid
        valid_methods = PaymentTypeEnum.load_from_midtrans()
        if value not in valid_methods:
            raise ValueError(f"Tipe pembayaran tidak valid. Pilihan yang tersedia: {', '.join(valid_methods)}")
        return value
    
class PaymentCreateSchemaDto(BaseModel):
    order_id: str  # UUID dari order yang akan dibayar
    transaction_id: str
    payment_type: str
    gross_amount: float
    transaction_status: str
    payment_response: Optional[dict] = None

class PaymentResponseSchemaDto(BaseModel):
    id: str
    order_id: str
    transaction_id: str
    payment_type: str
    gross_amount: float
    transaction_status: str
    payment_response: Optional[dict]
    created_at: str
    updated_at: str

# DTO untuk respons dari Midtrans
class PaymentMidtransResponseDTO(BaseModel):
    transaction_id: str
    redirect_url: Optional[str]  # URL untuk diarahkan pengguna
    token: Optional[str]  # Token transaksi
    transaction_status: str  # Status transaksi seperti "pending", "settlement"


class PaymentInfoResponseDto(BaseModel):
    status_code: int = Field(default=201)
    message: str = Field(default="Your payment has been created")
    data: PaymentMidtransResponseDTO

class InfoTransactionIdDto(BaseModel):
    order_id: str

class PaymentNotificationSchemaDto(BaseModel):
    order_id: str
    transaction_status: TransactionStatusEnum  # Menggunakan Enum di DTO
    fraud_status: FraudStatusEnum  # Menggunakan Enum di DTO

class PaymentNotificationResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Success access")
    data: PaymentNotificationSchemaDto

class MidtransNotificationDto(BaseModel):
    order_id: str
    transaction_status: str
    fraud_status: str
    payment_type: str
    gross_amount: str
    signature_key: str
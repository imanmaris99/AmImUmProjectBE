from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import FraudStatusEnum, PaymentTypeEnum, TransactionStatusEnum

class PaymentOrderByIdDto(BaseModel):
    order_id: str  # UUID dari order yang akan dibayar

class PaymentCreateDto(BaseModel):
    order_id: str  # UUID dari order yang akan dibayar
    payment_type: str  # Jenis pembayaran (credit_card, gopay, bank_transfer, dll.)

    @field_validator("payment_type")
    @classmethod
    def validate_payment_type(cls, value: str) -> str:
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

class AdminPaymentInfoDto(BaseModel):
    id: str
    order_id: str
    transaction_id: str
    payment_type: Optional[str] = None
    gross_amount: float = 0.0
    transaction_status: Optional[str] = None
    fraud_status: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    order_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AdminPaymentDetailDto(AdminPaymentInfoDto):
    payment_response: Optional[dict] = None

class AdminListMetaDto(BaseModel):
    skip: int = 0
    limit: int = 100
    count: int = 0

class AdminPaymentListResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Admin payment list accessed successfully")
    data: list[AdminPaymentInfoDto]
    meta: Optional[AdminListMetaDto] = None

class AdminPaymentDetailResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Admin payment detail accessed successfully")
    data: AdminPaymentDetailDto

# class MidtransNotificationDto(BaseModel):
#     order_id: str
#     transaction_status: str
#     fraud_status: str
#     payment_type: str
#     gross_amount: str
#     signature_key: str

# class MidtransNotificationDto(BaseModel):
#     order_id: str
#     transaction_status: Optional[str] = None
#     fraud_status: str
#     payment_type: Optional[str] = None
#     gross_amount: Optional[str] = None
#     signature_key: Optional[str] = None

class MidtransNotificationDto(BaseModel):
    order_id: str = Field(..., description="ID pesanan unik yang diberikan oleh sistem.")
    transaction_status: Optional[str] = Field(
        None,
        description="Status transaksi dari Midtrans, seperti 'settlement', 'pending', atau 'cancel'."
    )
    status_code: Optional[str] = Field(
        None,
        description="HTTP-like status code dari payload callback Midtrans, biasanya string seperti '200'."
    )
    fraud_status: Optional[str] = Field(
        None,
        description="Status penipuan (fraud) dari Midtrans, biasanya bernilai 'accept' atau 'deny'."
    )
    payment_type: Optional[str] = Field(
        None,
        description="Jenis pembayaran seperti 'credit_card', 'bank_transfer', atau lainnya."
    )
    gross_amount: Optional[str] = Field(
        None,
        description="Jumlah pembayaran dalam bentuk string untuk mendukung format dari Midtrans."
    )
    signature_key: Optional[str] = Field(
        None,
        description="Kunci tanda tangan yang digunakan untuk validasi keamanan."
    )
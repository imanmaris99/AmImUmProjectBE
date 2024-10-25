import uuid
from sqlalchemy import Column, String, DECIMAL, JSON, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class PaymentModel(Base):
    __tablename__ = "payments"
    
    # Menggunakan UUID untuk ID payment
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    order_id = Column(CHAR(36), ForeignKey("orders.id"), nullable=False, unique=True, index=True)  # UUID from OrderModel
    transaction_id = Column(String(255), unique=True, nullable=False)  # ID transaksi dari Midtrans
    payment_type = Column(String(50), nullable=False)  # e.g., credit_card, bank_transfer
    gross_amount = Column(DECIMAL(10, 2), nullable=False)
    transaction_status = Column(String(50), nullable=False)  # e.g., pending, settlement, expire
    payment_response = Column(JSON, nullable=True)  # menyimpan respon lengkap dari Midtrans
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # order = relationship("OrderModel", back_populates="payment", lazy='selectin')  # Optimized eager loading with 'selectin'
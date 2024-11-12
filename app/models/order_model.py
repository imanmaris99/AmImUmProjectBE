import enum
import uuid
from sqlalchemy import Column, Enum, String, DECIMAL, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.libs.sql_alchemy_lib import Base


class DeliveryTypeEnum(enum.Enum):
    delivery = "delivery"
    pickup = "pickup"

class OrderModel(Base):
    __tablename__ = "orders"
    
    # Menggunakan UUID untuk ID order
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    status = Column(String(15), nullable=False)  # e.g., pending, paid, shipped
    total_price = Column(DECIMAL(10, 2), nullable=False)
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True, index=True)  # member or non-member
    shipment_id = Column(CHAR(36), ForeignKey("shipments.id"), nullable=True, index=True)
    delivery_type = Column(Enum(DeliveryTypeEnum), nullable=False, default=DeliveryTypeEnum.delivery)  # Tambahkan Enum
    notes = Column(String(100), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # customer = relationship(
    #     "UserModel",
    #     back_populates="orders",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # shipment = relationship(
    #     "ShipmentModel",
    #     back_populates="order",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # order_items = relationship(
    #     "OrderItemModel",
    #     back_populates="order",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading jika diperlukan
    # )
    # payment = relationship(
    #     "PaymentModel",
    #     back_populates="order",
    #     uselist=False,
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )

    shipment: Mapped["ShipmentModel"] = relationship(
        "ShipmentModel", 
        back_populates="", 
    )

    # cart: Mapped[list["CartProductModel"]] = relationship(
    #     "CartProductModel", 
    #     back_populates="", 
    # )
    
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates=""
    )

    def __repr__(self):
        # Mengonversi UUID biner kembali ke format string untuk representasi yang lebih mudah dibaca
        return f"<Order(id='{self.id}', status='{self.status}', total_price={self.total_price})>"
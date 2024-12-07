import enum

import uuid
from sqlalchemy import Column, Enum, String, DECIMAL, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped

from app.dtos import order_dtos

from app.dtos.shipment_dtos import MyShipmentAddressOrderInfoDto
from app.libs.sql_alchemy_lib import Base
from app.models.enums import DeliveryTypeEnum


# class DeliveryTypeEnum(enum.Enum):
#     delivery = "delivery"
#     pickup = "pickup"

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
    # payment = relationship(
    #     "PaymentModel",
    #     back_populates="order",
    #     uselist=False,
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # cart: Mapped[list["CartProductModel"]] = relationship(
    #     "CartProductModel", 
    #     back_populates="", 
    # )
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates=""
    )

    shipments: Mapped["ShipmentModel"] = relationship(
        "ShipmentModel", 
        back_populates="", 
    )

    order_items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading jika diperlukan
    )
    
    payment: Mapped["PaymentModel"] = relationship(
        "PaymentModel",
        back_populates="order",
        uselist=False,
        lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading jika diperlukan
    )
    
    def __repr__(self):
        return f"<Order(id={self.id}, status={self.status}, delivery_type={self.delivery_type})>"
    

    @property
    def customer_name(self) -> str:
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.firstname if user_models else ""

    @property
    def customer_email(self) -> str:
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.email if user_models else ""

    @property
    def customer_phone(self) -> str:
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.phone if user_models else ""

    @property
    def shipping_cost(self) -> float:
        from app.models.shipment_model import ShipmentModel
        shipment_models: ShipmentModel = self.shipments
        return shipment_models.shipping_cost if shipment_models else 0.0

    @property
    def my_shipping(self):
        from app.models import ShipmentAddressModel
        address_model: ShipmentAddressModel = self.shipments
        return MyShipmentAddressOrderInfoDto(
            id=address_model.id,
            my_courier=address_model.my_courier,
            my_address=address_model.my_address,
            created_at=address_model.created_at
        ).model_dump() if address_model else None

    @property
    def order_item_lists(self):
        return [
            order_dtos.OrderItemDto(
                id=order_item.id,
                product_name=order_item.product_name,
                variant_product=order_item.variant_product,
                variant_discount=order_item.variant_discount,
                quantity=order_item.quantity,
                price_per_item=order_item.price_per_item,
                total_price=order_item.total_price,
                created_at=order_item.created_at
            ).model_dump() for order_item in self.order_items
        ] if self.order_items else []
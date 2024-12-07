import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped

from app.dtos.shipment_dtos import MyShipmentAddressInfoDto, MyCourierInfoDto

from app.libs.sql_alchemy_lib import Base

class ShipmentModel(Base):
    __tablename__ = "shipments"
    
    # Menggunakan UUID untuk ID shipment
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    code_tracking = Column(String(50), nullable=False, index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=False, index=True)  # Integer from CourierModel
    is_active = Column(Boolean, default=True)
    address_id = Column(Integer, ForeignKey("shipment_addresses.id"), nullable=True)  # Integer from ShipmentAddressModel
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True)  # UUID from UserModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # courier = relationship("CourierModel", back_populates="shipments", lazy='selectin')  # Ganti eager loading ke selectin untuk efisiensi
    # shipment_address = relationship("ShipmentAddressModel", back_populates="shipments", lazy='selectin')  # Ganti eager loading ke selectin
    # order = relationship("OrderModel", back_populates="shipment", uselist=False, lazy='selectin')  # Ganti eager loading ke selectin
    courier: Mapped["CourierModel"] = relationship(
        "CourierModel", 
        back_populates="shipments", 
        lazy='selectin')  # Optimasi eager loading

    shipment_address: Mapped["ShipmentAddressModel"] = relationship(
        "ShipmentAddressModel",
        back_populates="shipments",
        lazy="selectin"  # Optimized eager loading
    )    

    order: Mapped[list["OrderModel"]] = relationship(
        "OrderModel", 
        back_populates="shipments", 
        lazy="selectin")  # Lazy loading

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates=""
    )
    
    def __repr__(self):
        return f"<Shipment(id='{self.id}')>"

    @property
    def my_address(self):
        from app.models import ShipmentAddressModel
        address_model: ShipmentAddressModel = self.shipment_address
        return MyShipmentAddressInfoDto(
            id=address_model.id,
            name=address_model.name,
            phone=address_model.phone,
            address=address_model.address,
            created_at=address_model.created_at
        ).model_dump()

    @property
    def my_courier(self):
        from app.models import CourierModel
        courier_model: CourierModel = self.courier
        return MyCourierInfoDto(
            id=courier_model.id,
            courier_name=courier_model.courier_name,
            weight=courier_model.weight,
            service_type=courier_model.service_type,
            cost=courier_model.cost,
            estimated_delivery=courier_model.estimated_delivery,
            created_at=courier_model.created_at
        ).model_dump()

    # Properti untuk harga pengiriman
    @property
    def shipping_cost(self):
        from app.models.courier_model import CourierModel
        courier_models: CourierModel = self.courier
        return courier_models.cost if courier_models else ""
    
    @property
    def user_name(self):
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.firstname if user_models else ""
    
    @property
    def user_phone(self):
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.phone if user_models else ""
    
    @property
    def user_address(self):
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.address if user_models else ""
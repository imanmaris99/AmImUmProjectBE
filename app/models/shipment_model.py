import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class ShipmentModel(Base):
    __tablename__ = "shipments"
    
    # Menggunakan UUID untuk ID shipment
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    code_tracking = Column(String(50), nullable=False, index=True)
    courier_id = Column(Integer, ForeignKey("couriers.id"), nullable=False, index=True)  # Integer from CourierModel
    is_active = Column(Boolean, default=True)
    address_id = Column(Integer, ForeignKey("shipment_addresses.id"), nullable=True)  # Integer from ShipmentAddressModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # courier = relationship("CourierModel", back_populates="shipments", lazy='selectin')  # Ganti eager loading ke selectin untuk efisiensi
    # shipment_address = relationship("ShipmentAddressModel", back_populates="shipments", lazy='selectin')  # Ganti eager loading ke selectin
    # order = relationship("OrderModel", back_populates="shipment", uselist=False, lazy='selectin')  # Ganti eager loading ke selectin

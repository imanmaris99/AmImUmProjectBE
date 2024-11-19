from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.libs.sql_alchemy_lib import Base

class ShipmentAddressModel(Base):
    __tablename__ = "shipment_addresses"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False)
    city_id = Column(Integer, nullable=True)
    state = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    zip_code = Column(String(10), nullable=False)
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True)  # UUID from UserModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # customer = relationship("UserModel", back_populates="shipment_addresses", lazy='select')  # Lazy loading
    # shipments = relationship("ShipmentModel", back_populates="shipment_address", lazy='select')  # Lazy loading
    shipments: Mapped["ShipmentModel"] = relationship(
        "ShipmentModel", 
        back_populates="shipment_address", 
        lazy='selectin')  # Optimasi eager loading
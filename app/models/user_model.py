import uuid
from sqlalchemy import Column, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.libs.sql_alchemy_lib import Base


class UserModel(Base):
    __tablename__ = "users"

    # Using UUID for user ID
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    firstname = Column(String(15), nullable=True)
    lastname = Column(String(15), nullable=True)
    fullname = Column(String(50), nullable=True)
    gender = Column(String(10), nullable=True)
    email = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(50), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    hash_password = Column(String(100), nullable=True)
    photo_url = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False)
    firebase_uid = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    verification_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    cart_products: Mapped[list["CartProductModel"]] = relationship(
        "CartProductModel",
        back_populates="user",
        lazy="selectin"
    )

    orders: Mapped[list["OrderModel"]] = relationship(
        "OrderModel",
        back_populates="user",
        lazy="selectin"
    )

    shipments: Mapped[list["ShipmentModel"]] = relationship(
        "ShipmentModel",
        back_populates="user",
        lazy="selectin"
    )

    couriers: Mapped[list["CourierModel"]] = relationship(
        "CourierModel",
        back_populates="user",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<User(id='{self.id}', phone='{self.phone}')>" 


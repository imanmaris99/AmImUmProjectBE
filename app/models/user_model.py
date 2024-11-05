import uuid
from sqlalchemy import Column, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # cart_products = relationship("CartProductModel", back_populates="customer", lazy='select')  # Lazy loading
    # wishlists = relationship("WishlistModel", back_populates="customer", lazy='select')  # Lazy loading
    # orders = relationship("OrderModel", back_populates="customer", lazy='selectin')  # Optimized eager loading
    # shipment_addresses = relationship("ShipmentAddressModel", back_populates="customer", lazy='select')  # Lazy loading
    # ratings = relationship("RatingModel", back_populates="user", lazy='select')  # Lazy loading

    def __repr__(self):
        return f"<User(id='{self.id}', phone='{self.phone}')>" 


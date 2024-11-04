from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class CartProductModel(Base):
    __tablename__ = "cart_products"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    quantity = Column(Integer, nullable=False)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)  # UUID from ProductModel
    variant_id = Column(Integer, ForeignKey("pack_types.id"), nullable=False, index=True)  
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)  # UUID from UserModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    
    # Relationships
    # product = relationship(
    #     "ProductModel",
    #     back_populates="cart_products",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # customer = relationship(
    #     "UserModel",
    #     back_populates="cart_products",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
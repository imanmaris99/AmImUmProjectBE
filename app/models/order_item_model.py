from sqlalchemy import Column, Integer, DECIMAL, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class OrderItemModel(Base):
    __tablename__ = "order_items"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    quantity = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)  # UUID from ProductModel
    order_id = Column(CHAR(36), ForeignKey("orders.id"), nullable=False, index=True)  # UUID from OrderModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # product = relationship(
    #     "ProductModel",
    #     back_populates="order_items",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # order = relationship(
    #     "OrderModel",
    #     back_populates="order_items",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    
    def __repr__(self):
        # Mengonversi UUID biner kembali ke format string untuk representasi yang lebih mudah dibaca
        return f"<OrderItem(id={self.id}, quantity={self.quantity}, price={self.price}, product_id='{self.product_id}', order_id='{self.order_id}')>"
    
from sqlalchemy import Column, Integer, DECIMAL, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.libs.sql_alchemy_lib import Base

class OrderItemModel(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    order_id = Column(CHAR(36), ForeignKey("orders.id"), nullable=False, index=True)  # UUID dari OrderModel
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)  # UUID dari ProductModel
    variant_id = Column(Integer, ForeignKey("pack_types.id"), nullable=True, index=True)  # Jika ada varian
    quantity = Column(Integer, nullable=False)  # Kuantitas yang dipesan
    price_per_item = Column(DECIMAL(10, 2), nullable=False)  # Harga per item pada saat pesanan dibuat
    total_price = Column(DECIMAL(10, 2), nullable=False)  # Total harga untuk item ini (quantity * price_per_item)
    
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
    
    products: Mapped["ProductModel"] = relationship(
        "ProductModel",
        back_populates="",
    )

    pack_type: Mapped["PackTypeModel"] = relationship(
        "PackTypeModel", 
        back_populates="", 
    )

    order: Mapped[list["OrderModel"]] = relationship(
        "OrderModel", 
        back_populates="", 
    )
    
    # user: Mapped["UserModel"] = relationship(
    #     "UserModel",
    #     back_populates=""
    # )

    def __repr__(self):
        # Mengonversi UUID biner kembali ke format string untuk representasi yang lebih mudah dibaca
        return f"<OrderItem(id={self.id}, quantity={self.quantity}, price={self.price}, product_id='{self.product_id}', order_id='{self.order_id}')>"
    
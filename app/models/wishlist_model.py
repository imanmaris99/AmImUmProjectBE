from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class WishlistModel(Base):
    __tablename__ = "wishlists"
    
    # Using Integer for ID with autoincrement
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)  # UUID from ProductModel
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)  # UUID from UserModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # product = relationship("ProductModel", back_populates="wishlists", lazy='selectin')  # Optimized eager loading
    # customer = relationship("UserModel", back_populates="wishlists", lazy='select')  # Lazy loading

    def __repr__(self):
        return f"<Wishlist(id={self.id}, product_id={self.product_id}, customer_id={self.customer_id})>"

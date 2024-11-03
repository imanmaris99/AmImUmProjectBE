from typing import Any, Dict, Optional
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.libs.sql_alchemy_lib import Base

class WishlistModel(Base):
    __tablename__ = "wishlists"
    
    # Using Integer for ID with autoincrement
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)  # UUID from ProductModel
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)  # UUID from UserModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    products: Mapped["ProductModel"] = relationship(
        "ProductModel",
        back_populates="",
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates=""
    )
    def __repr__(self):
        return f"<Wishlist(id={self.id}, product_id={self.product_id}, customer_id={self.customer_id})>"

    @property
    def product_name(self) -> str:
        from app.models.product_model import ProductModel
        products_model: ProductModel = self.products
        return products_model.name if products_model else ""

    @property
    def product_variant(self) -> Optional[Dict[str, Any]]:
        from app.models.product_model import ProductModel
        
        # Pastikan self.products adalah instance ProductModel atau memiliki relationship ke ProductModel
        products_model: Optional[ProductModel] = self.products
        if products_model:
            return products_model.all_variants
        return None  # Mengembalikan None jika products_model tidak ada
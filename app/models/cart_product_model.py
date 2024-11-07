from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.dtos import pack_type_dtos
from app.libs.sql_alchemy_lib import Base

class CartProductModel(Base):
    __tablename__ = "cart_products"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    quantity = Column(Integer, nullable=False)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)  # UUID from ProductModel
    variant_id = Column(Integer, ForeignKey("pack_types.id"), nullable=False, index=True)  
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)  # UUID from UserModel
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    products: Mapped["ProductModel"] = relationship(
        "ProductModel",
        back_populates="",
    )

    pack_type: Mapped[list["PackTypeModel"]] = relationship(
        "PackTypeModel", 
        back_populates="", 
    )
    
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates=""
    )

    def __repr__(self):
        return f"<Cart(id={self.id}, product_id={self.product_id}, variant_id={self.variant_id}, customer_id={self.customer_id})>"

    # Properti untuk nama produk
    @property
    def customer_name(self):
        return self.user.firstname if self.user else ""

    # Properti untuk nama produk
    @property
    def product_name(self):
        return self.products.name if self.products else ""
    
    # Properti untuk harga produk tanpa promo
    @property
    def product_price(self):
        return self.products.price if self.products else 0
    
    # Properti untuk variant produk
    @property
    def variant_product(self):
        return self.pack_type.variant if self.pack_type else 0

    # Properti untuk harga promo (diskon)
    @property
    def promo(self):
        return float(self.pack_type.promo) if self.pack_type and self.pack_type.promo else 0
    
    # Total promo yang diterapkan
    @property
    def total_promo(self):
        promo_amount = self.promo
        return promo_amount * self.quantity if promo_amount else 0
    
    # Total harga tanpa diskon
    @property
    def total_price_no_discount(self):
        price = self.product_price
        return price * self.quantity if price else 0
    
    # Total harga setelah diskon
    @property
    def total_price_with_discount(self):
        price_after_discount = self.product_price - self.promo
        return max(price_after_discount, 0) * self.quantity if price_after_discount else 0
    
    # Total harga berdasarkan apakah ada promo atau tidak
    @property
    def total_price(self):
        # Jika ada promo, gunakan harga setelah diskon, jika tidak, harga tanpa diskon
        return self.total_price_with_discount if self.promo else self.total_price_no_discount
        
    @property
    def variant_info(self) -> Optional[Dict[str, Any]]:
        return {
            pack_type_dtos.VariantProductDto(
                id=variant.id,
                product=variant.product,
                name=variant.name,
                img=variant.img,
                variant=variant.variant,
                expiration=variant.expiration,
                stock=variant.stock,
                discount=variant.discount,
                discounted_price=float(variant.discounted_price),
                updated_at=variant.updated_at
            ).model_dump() for variant in self.pack_type
        }

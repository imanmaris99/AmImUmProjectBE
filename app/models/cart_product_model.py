from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.dtos import pack_type_dtos
from app.libs.sql_alchemy_lib import Base

class CartProductModel(Base):
    __tablename__ = "cart_products"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    quantity = Column(Integer, nullable=False)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("pack_types.id"), nullable=False, index=True)
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    products: Mapped["ProductModel"] = relationship(
        "ProductModel",
        back_populates="",
    )

    pack_type: Mapped["PackTypeModel"] = relationship(
        "PackTypeModel", 
        back_populates="", 
    )
    
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="cart_products",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Cart(id={self.id}, product_id={self.product_id}, variant_id={self.variant_id}, customer_id={self.customer_id})>"

    @property
    def customer_name(self):
        return self.user.firstname if self.user else ""

    @property
    def product_name(self):
        return self.products.name if self.products else ""
    
    @property
    def product_price(self):
        if self.pack_type and self.pack_type.price is not None:
            return self.pack_type.price
        return self.products.price if self.products else 0
    
    @property
    def variant_product(self):
        return self.pack_type.variant if self.pack_type else 0

    @property
    def promo(self):
        if self.pack_type and self.pack_type.discount_amount is not None:
            return Decimal(str(self.pack_type.discount_amount))
        return Decimal("0")
    
    @property
    def total_promo(self):
        promo_amount = self.promo
        return promo_amount * self.quantity if promo_amount else Decimal("0")
    
    @property
    def total_price_no_discount(self):
        price = Decimal(str(self.product_price or 0))
        return price * self.quantity if price else Decimal("0")
    
    @property
    def total_price_with_discount(self):
        product_price = Decimal(str(self.product_price or 0))
        price_after_discount = product_price - self.promo
        return max(price_after_discount, Decimal("0")) * self.quantity if price_after_discount else Decimal("0")
    
    @property
    def total_price(self):
        return self.total_price_with_discount if self.promo > 0 else self.total_price_no_discount
        
    @property
    def variant_info(self) -> Optional[Dict[str, Any]]:
        if not self.pack_type:
            return None

        variant = self.pack_type
        return pack_type_dtos.VariantProductCartDto(
            id=variant.id,
            variant=variant.variant,
            name=variant.name,
            img=variant.img,
            price=float(variant.base_price),
            discount=variant.discount,
            discounted_price=float(variant.discounted_price),
        ).model_dump()

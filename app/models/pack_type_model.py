from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import Column, Float, ForeignKey, String, Integer, DateTime, func, DECIMAL
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.mysql import CHAR
from app.libs import sql_alchemy_lib

class PackTypeModel(sql_alchemy_lib.Base):
    __tablename__ = "pack_types"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False, index=True)
    img = Column(String(200), nullable=True)
    name = Column(String(50), nullable=False)
    min_amount = Column(Integer, nullable=False)
    variant = Column(String(25), nullable=True)
    expiration = Column(String(15), nullable=True)
    stock = Column(Integer, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    discount = Column(Float, nullable=True, index=True)
    fk_admin_id = Column(CHAR(36), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
        
    # Relationships
    products: Mapped["ProductModel"]= relationship(
        "ProductModel",
        back_populates="pack_type",
        lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    )

    def __repr__(self):
        return f"<PackType(variant='{self.variant}', name='{self.name}', id={self.id})>"
    
    @property
    def product(self):
        return self.products.name if self.products else ""

    @property
    def base_price(self) -> Decimal:
        if self.price is None:
            return Decimal("0.00")
        return Decimal(str(self.price))

    @property
    def discount_amount(self) -> Decimal:
        if not self.discount:
            return Decimal("0.00")
        discount_value = Decimal(str(self.discount))
        return (self.base_price * (discount_value / Decimal("100"))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def promo(self):
        return self.discount_amount

    @property
    def discounted_price(self):
        discounted = self.base_price - self.discount_amount
        return discounted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # @property
    # def discounted_price(self):
    #     if not self.products or self.products.price is None:
    #         return 0
    #     price = self.products.price
    #     if self.discount:
    #         return round(price - (price * self.discount), 2)
    #     return price
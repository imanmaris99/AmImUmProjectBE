from decimal import Decimal
from sqlalchemy import Column, Float, ForeignKey, String, Integer, DateTime, func
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.dialects.mysql import CHAR
from app.libs import sql_alchemy_lib

class PackTypeModel(sql_alchemy_lib.Base):
    __tablename__ = "pack_types"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=True)  # UUID from ProductModel
    img = Column(String(200), nullable=True)
    name = Column(String(50), nullable=False)  # gram/dosh/sachet
    min_amount = Column(Integer, nullable=False)
    variant = Column(String(25), nullable=True)
    expiration = Column(String(15), nullable=True)  # Ganti ke DateTime jika mengacu pada tanggal
    stock = Column(Integer, nullable=False)
    discount = Column(Float, nullable=True, index=True)  # Menggunakan Float untuk persentase dengan desimal
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
    def discounted_price(self):
        if not self.products or self.products.price is None:
            return Decimal(0)
        price = Decimal(self.products.price)
        if self.discount:
            discount_value = Decimal(self.discount)  # Ubah diskon ke Decimal
            return round(price - (price * (discount_value / Decimal(100))), 2)
        return price

    # @property
    # def discounted_price(self):
    #     if not self.products or self.products.price is None:
    #         return 0
    #     price = self.products.price
    #     if self.discount:
    #         return round(price - (price * self.discount), 2)
    #     return price
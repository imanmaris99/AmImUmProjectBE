from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped
from app.libs import sql_alchemy_lib

class ProductionModel(sql_alchemy_lib.Base):
    __tablename__ = "productions"  # Menggunakan bentuk jamak untuk konsistensi
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # Menambahkan unique constraint dan indeks
    herbal_category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=False, index=True)  # Menambahkan indeks
    photo_url = Column(String(255), nullable=True)
    description : str = Column(String(1000), nullable=True)  # Menggunakan String dengan batas karakter jika deskripsi tidak terlalu panjang
    fk_admin_id = Column(CHAR(36), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)  # Menambahkan kolom updated_at

 # Relationships
    herbal_category: Mapped["TagCategoryModel"] = relationship(
        "TagCategoryModel",
        back_populates="product_bies",
        lazy="selectin"
        )

    products: Mapped[list["ProductModel"]] = relationship(
        "ProductModel",
        back_populates="product_bies",
        lazy="selectin"  # Optimized eager loading
    )

    def __repr__(self):
        return f"<Production(name='{self.name}', id={self.id})>"
    
    @property
    def description_list(self):
        if not self.description:
            return []
        return [d.strip() for d in self.description.splitlines() if d.strip()]
    
    @property
    def category(self):
        return self.herbal_category.name if self.herbal_category else ""
    
    # @property
    # def promo_special(self):
    #     return self.products.highest_promo if self.products else 0
    @property
    def promo_special(self) -> float:
        """Mengembalikan promo tertinggi dari produk, jika ada."""
        if self.products:
            return max((product.highest_promo for product in self.products), default=0)
        return 0
    
    @property
    def total_product(self):
        return len(self.products)
    
    @property
    def total_product_with_promo(self):
        """Menghitung jumlah produk dengan promo."""
        if not self.products:
            return 0
        return sum(1 for product in self.products if product.highest_promo > 0)

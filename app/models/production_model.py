from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.libs import sql_alchemy_lib

class ProductionModel(sql_alchemy_lib.Base):
    __tablename__ = "productions"  # Menggunakan bentuk jamak untuk konsistensi
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # Menambahkan unique constraint dan indeks
    herbal_category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=False, index=True)  # Menambahkan indeks
    description : str = Column(String(1000), nullable=True)  # Menggunakan String dengan batas karakter jika deskripsi tidak terlalu panjang
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)  # Menambahkan kolom updated_at
    
    # Relationships
    # herbal_category = relationship(
    #     "TagCategoryModel",
    #     back_populates="product_bies",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # products = relationship(
    #     "ProductModel",
    #     back_populates="product_by",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading jika perlu
    # )
    
    def __repr__(self):
        return f"<Production(name='{self.name}', id={self.id})>"

    @property
    def description_list(self):
        if not self.description:
            return []
        # Memecah deskripsi berdasarkan baris baru menggunakan splitlines()
        return [d.strip() for d in self.description.splitlines() if d.strip()]
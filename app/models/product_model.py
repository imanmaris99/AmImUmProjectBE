import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Boolean, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs import sql_alchemy_lib

class ProductModel(sql_alchemy_lib.Base):
    __tablename__ = "products"
    
    # Menggunakan UUID untuk ID produk
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # Menambahkan indeks jika sering dicari
    info = Column(String(100), nullable=True)  # Content of the post
    weight = Column(Integer, nullable=False)
    pack_type_id = Column(Integer, ForeignKey("pack_types.id"), nullable=False)
    description : str = Column(Text, nullable=True)
    instruction : str = Column(Text, nullable=True)  # Content of instructions for use
    price = Column(DECIMAL(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    product_by_id = Column(Integer, ForeignKey("productions.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # pack_type = relationship("PackTypeModel", back_populates="products", lazy='selectin')  # Optimasi eager loading
    # product_by = relationship("ProductionModel", back_populates="products", lazy='selectin')  # Optimasi eager loading
    # ratings = relationship("RatingModel", back_populates="product", lazy='select')  # Lazy loading
    # order_items = relationship("OrderItemModel", back_populates="product", lazy='select')  # Lazy loading
    # cart_products = relationship("CartProductModel", back_populates="product", lazy='select')  # Lazy loading
    # wishlists = relationship("WishlistModel", back_populates="product", lazy='select')  # Lazy loading


    def __repr__(self):
        # Mengonversi UUID biner kembali ke format string untuk representasi yang lebih mudah dibaca
        return f"<Product(name='{self.name}', id='{self.id}')>"
    
    @property
    def description_list(self):
        if not self.description:
            return []
        # Memecah deskripsi berdasarkan baris baru menggunakan splitlines()
        return [d.strip() for d in self.description.splitlines() if d.strip()]
    
    @property
    def instruction_list(self):
        if not self.instruction:
            return []
        # Memecah instruksi berdasarkan baris baru menggunakan splitlines()
        return [i.strip() for i in self.instruction.splitlines() if i.strip()]
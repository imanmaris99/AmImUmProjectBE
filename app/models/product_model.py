import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Boolean, func
from sqlalchemy.dialects.mysql import CHAR
from decimal import Decimal
from sqlalchemy.orm import relationship, Mapped
from app.dtos import product_dtos
from app.libs import sql_alchemy_lib

class ProductModel(sql_alchemy_lib.Base):
    __tablename__ = "products"
    
    # Menggunakan UUID untuk ID produk
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    name = Column(String(100), nullable=False, index=True)  # Menambahkan indeks jika sering dicari
    info = Column(String(100), nullable=True)  # Content of the post
    weight = Column(Integer, nullable=False)
    description : str = Column(Text, nullable=True)
    instruction : str = Column(Text, nullable=True)  # Content of instructions for use
    price = Column(DECIMAL(10, 2), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    product_by_id = Column(Integer, ForeignKey("productions.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    pack_type: Mapped[list["PackTypeModel"]] = relationship(
        "PackTypeModel", 
        back_populates="products", 
        lazy='selectin')  # Optimasi eager loading

    product_bies: Mapped["ProductionModel"] = relationship(
        "ProductionModel",
        back_populates="products",
        lazy="selectin"  # Optimized eager loading
    )    

    ratings: Mapped[list["RatingModel"]] = relationship(
        "RatingModel", 
        back_populates="products", 
        lazy='select')  # Lazy loading
    
    def __repr__(self):
        return f"<Product(name='{self.name}', id='{self.id}')>"

    # Properti yang memecah deskripsi dan instruksi berdasarkan baris baru
    @property
    def description_list(self):
        return [d.strip() for d in self.description.splitlines() if d.strip()] if self.description else []

    @property
    def instruction_list(self):
        return [i.strip() for i in self.instruction.splitlines() if i.strip()] if self.instruction else []

    # Properti untuk mendapatkan nama perusahaan terkait
    @property
    def company(self):
        return self.product_bies.name if self.product_bies else ""
    
    @property
    def highest_promo(self):
        if not self.pack_type:
            return 0
        # Mengambil nilai diskon tertinggi dari pack_type
        max_discount = max((pt.discount for pt in self.pack_type if pt.discount), default=0)
        return round(max_discount, 1)

    # Properti untuk menghitung rata-rata promo
    @property
    def avg_promo(self):
        if not self.pack_type:
            return 0
        total_discount = sum(pt.discount for pt in self.pack_type if pt.discount)
        return round(total_discount / len(self.pack_type), 1) if self.pack_type else 0

    # Properti untuk menghitung rata-rata rating
    @property
    def avg_rating(self):
        if not self.ratings:
            return 0
        total_rating = sum(r.rating_count for r in self.ratings)
        return round(total_rating / len(self.ratings), 1) if self.ratings else 0

    @property
    def total_rater(self):
        return len(self.ratings)

    # Properti untuk mendapatkan semua varian produk
    @property
    def all_variants(self):
        return [
            product_dtos.VariantAllProductDto(
                id=variant.id,
                variant=variant.variant,
                discount=variant.discount,
                discounted_price=float(variant.discounted_price),
                updated_at=variant.updated_at
            ).model_dump() for variant in self.pack_type
        ] if self.pack_type else []

    # Properti untuk mendapatkan daftar varian produk
    @property
    def variants_list(self):
        return [
            product_dtos.VariantProductDto(
                id=variant.id,
                product=variant.product,
                variant=variant.variant,
                expiration=variant.expiration,
                stock=variant.stock,
                discount=variant.discount,
                discounted_price=float(variant.discounted_price),
                updated_at=variant.updated_at
            ).model_dump() for variant in self.pack_type
        ] if self.pack_type else []

    # Properti untuk mendapatkan daftar rating produk
    @property
    def rating_list(self):
        return [
            product_dtos.ProductRatingDto(
                id=rating.id,
                rating_count=rating.rate,
                review_description=rating.review,
                rater_name=rating.rater_name
            ).model_dump() for rating in self.ratings
        ] if self.ratings else []
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
    
    @property
    def company(self):
        return self.product_bies.name if self.product_bies else ""
    
    @property
    def avg_promo(self):
        if not self.pack_type:
            return 0
        total_discount = sum(discounted.discount for discounted in self.pack_type if discounted.discount)
        average_discount = total_discount / len(self.pack_type) if self.pack_type else 0
        return round(average_discount, 1)

    @property
    def avg_rating(self):
        if not self.ratings:  # Menggunakan relasi ratings langsung
            return 0
        total_rating = sum(rating.rating_count for rating in self.ratings)
        average_rating = total_rating / len(self.ratings) if self.pack_type else 0
        return round(average_rating, 1)

    @property
    def total_rater(self):
        return len(self.ratings)

    @property
    def all_variants(self):
        from app.models.pack_type_model import PackTypeModel
        pack_type_dtos = []
        all_variants: list[PackTypeModel] = self.pack_type if self.pack_type else []
        
        for type in all_variants:
            all_variant_dto = product_dtos.VariantAllProductDto(
                id=type.id,
                variant=type.variant,
                discount=type.discount,
                discounted_price=float(type.discounted_price),  # Mengembalikan ke float jika perlu
                updated_at=type.updated_at
            ).model_dump()
            pack_type_dtos.append(all_variant_dto)
        
        return pack_type_dtos


    @property
    def variants_list(self):
        from app.models.pack_type_model import PackTypeModel
        pack_type_dtos = []
        variants_list: list[PackTypeModel] = self.pack_type if self.pack_type else []
        
        for variants in variants_list:
            variant_dto = product_dtos.VariantProductDto(
                id= variants.id,
                product=variants.product,
                variant= variants.variant,
                expiration= variants.expiration,
                stock= variants.stock,
                discount= variants.discount,
                discounted_price=float(variants.discounted_price),
                updated_at=variants.updated_at
            ).model_dump()
            pack_type_dtos.append(variant_dto)

        return pack_type_dtos

    @property
    def rating_list(self):
        from app.models.rating_model import RatingModel
        rating_dtos = []
        rating_list: list[RatingModel] = self.ratings if self.ratings else []
        for rating in rating_list:
            rating_dto = product_dtos.ProductRatingDto(
                id=rating.id,
                rating_count=rating.rate,
                review_description=rating.review,
                rater_name=rating.rater_name
            ).model_dump()
            rating_dtos.append(rating_dto)

        return rating_dtos
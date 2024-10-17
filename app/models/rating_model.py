from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class RatingModel(Base):
    __tablename__ = "ratings"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    rate = Column(Integer, nullable=False, index=True)  # Menambahkan indeks jika sering digunakan dalam filter atau pengurutan
    review = Column(String(100), nullable=True)  # Pertahankan jika 100 karakter sudah cukup
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=False)  # UUID from ProductModel
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)  # UUID from UserModel
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # product = relationship(
    #     "ProductModel",
    #     back_populates="ratings",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    # user = relationship(
    #     "UserModel",
    #     back_populates="ratings",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )

    def __repr__(self):
        # Mengonversi UUID biner kembali ke format string untuk representasi yang lebih mudah dibaca
        return f"<Rating(id={self.id}, rate={self.rate}, product_id='{self.product_id}', user_id='{self.user_id}')>"
    
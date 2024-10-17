from sqlalchemy import Column, Float, String, Integer, DateTime, func
from sqlalchemy.orm import relationship
from app.libs import sql_alchemy_lib

class PackTypeModel(sql_alchemy_lib.Base):
    __tablename__ = "pack_types"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    img = Column(String(200), nullable=True)
    name = Column(String(50), nullable=False)  # gram/dosh/sachet
    min_amount = Column(Integer, nullable=False)
    variant = Column(String(25), nullable=True)
    expiration = Column(String(15), nullable=True)  # Ganti ke DateTime jika mengacu pada tanggal
    stock = Column(Integer, nullable=False)
    discount = Column(Float, nullable=True)  # Menggunakan Float untuk persentase dengan desimal
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
        
    # Relationships
    # products = relationship(
    #     "ProductModel",
    #     back_populates="pack_type",
    #     lazy='selectin'  # Menggunakan selectin untuk optimasi eager loading
    # )
    
    def __repr__(self):
        return f"<PackType(variant='{self.variant}', name='{self.name}', id={self.id})>"
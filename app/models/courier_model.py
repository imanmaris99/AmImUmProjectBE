from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, ForeignKey, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, Mapped

from app.libs.sql_alchemy_lib import Base

class CourierModel(Base):
    __tablename__ = "couriers"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    courier_name = Column(String(15), nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    service_type = Column(String(30), nullable=True)  # e.g., "express", "standard"
    is_active = Column(Boolean, default=True)
    customer_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False, index=True)  # UUID from UserModel

    # Informasi Paket
    weight = Column(Integer, nullable=False)
    length = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Informasi dari API Rajaongkir
    cost = Column(Float, nullable=True)  # Biaya pengiriman
    estimated_delivery = Column(Integer, nullable=True)  # Estimasi waktu pengiriman (dalam hari)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # shipments = relationship("ShipmentModel", back_populates="courier", lazy='select')  # Lazy loading
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates=""
    )

    def __repr__(self):
        # Mengonversi UUID biner kembali ke format string untuk representasi yang lebih mudah dibaca
        return f"<Courier(id={self.id}, courier_name={self.courier_name}, user_id='{self.customer_id}')>"

    @property
    def user_name(self):
        from app.models.user_model import UserModel
        user_models: UserModel = self.user
        return user_models.firstname if user_models else ""
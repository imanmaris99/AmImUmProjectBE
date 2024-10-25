from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.orm import relationship
from app.libs.sql_alchemy_lib import Base

class CourierModel(Base):
    __tablename__ = "couriers"
    
    # Menggunakan Integer ID
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    courier_name = Column(String(15), nullable=False, index=True)
    weight = Column(Integer, nullable=False)
    length = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    # shipments = relationship("ShipmentModel", back_populates="courier", lazy='select')  # Lazy loading

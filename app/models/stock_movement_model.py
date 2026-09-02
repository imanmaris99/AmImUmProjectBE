import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, relationship

from app.libs.sql_alchemy_lib import Base


class StockMovementModel(Base):
    __tablename__ = "stock_movements"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    variant_id = Column(Integer, ForeignKey("pack_types.id"), nullable=False, index=True)
    product_id = Column(CHAR(36), ForeignKey("products.id"), nullable=True, index=True)
    movement_type = Column(String(20), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    stock_before = Column(Integer, nullable=True)
    stock_after = Column(Integer, nullable=True)
    actor_id = Column(CHAR(36), ForeignKey("users.id"), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    reference = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    variant: Mapped["PackTypeModel"] = relationship("PackTypeModel", lazy="selectin")

    def __repr__(self):
        return f"<StockMovement(variant_id={self.variant_id}, delta={self.delta}, type='{self.movement_type}')>"

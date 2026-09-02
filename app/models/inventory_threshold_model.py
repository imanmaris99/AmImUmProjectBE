from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import Mapped, relationship

from app.libs.sql_alchemy_lib import Base


class InventoryThresholdModel(Base):
    __tablename__ = "inventory_thresholds"

    variant_id = Column(Integer, ForeignKey("pack_types.id"), primary_key=True, index=True)
    min_threshold = Column(Integer, nullable=False, default=10)
    updated_by = Column(CHAR(36), ForeignKey("users.id"), nullable=True, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    variant: Mapped["PackTypeModel"] = relationship("PackTypeModel", lazy="selectin")

    def __repr__(self):
        return f"<InventoryThreshold(variant_id={self.variant_id}, min_threshold={self.min_threshold})>"

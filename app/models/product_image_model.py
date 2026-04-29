from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship

from app.libs import sql_alchemy_lib


class ProductImageModel(sql_alchemy_lib.Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)

    storage_provider = Column(String(20), nullable=False, default="local")
    file_path = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    mime_type = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    is_primary = Column(Boolean, nullable=False, default=False, index=True)
    sort_order = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("ProductModel", backref="product_images", lazy="selectin")

from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship, Mapped
from app.libs import sql_alchemy_lib

class TagCategoryModel(sql_alchemy_lib.Base):
    __tablename__ = "tag_categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)    
    name = Column(String(100), nullable=False)
    description : str = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
 # Relationships
    product_bies: Mapped[list["ProductionModel"]] = relationship("ProductionModel")
    
    def __init__(self, name: str, description: Optional[str] = None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<TagCategory(name='{self.name}', description={self.description})>"
    
    @property
    def description_list(self):
        if not self.description:
            return []
        return [d.strip() for d in self.description.splitlines() if d.strip()]
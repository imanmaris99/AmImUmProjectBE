from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import Session
from app.libs import sql_alchemy_lib

class ArticleModel(sql_alchemy_lib.Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)    
    title = Column(String(100), nullable=False)
    img = Column(String(200), nullable=True)
    description : str = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Atribut untuk menampilkan ID yang berurutan
    display_id = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<Article(title='{self.title}', id={self.id})>"
    
    @property
    def description_list(self):
        if not self.description:
            return []
        # Memecah deskripsi berdasarkan baris baru menggunakan splitlines()
        return [d.strip() for d in self.description.splitlines() if d.strip()]
    
    @staticmethod
    def set_display_id(db: Session):
        """Mengatur display_id berdasarkan jumlah artikel yang ada."""
        total_articles = db.query(ArticleModel).count()
        return total_articles + 1
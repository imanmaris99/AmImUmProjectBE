import uuid
import re
from sqlalchemy import Column, Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship, backref, Mapped

from app.libs import sql_alchemy_lib


class UserModel(sql_alchemy_lib.Base):
    __tablename__ = "users"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    firstname = Column(String(15))
    lastname = Column(String(15))
    fullname = Column(String(50))
    gender = Column(String(10))
    email = Column(String(50), unique=True, index=True)
    phone = Column(String(50), unique=True)
    address = Column(Text)
    hash_password = Column(String(100))
    photo_url = Column(String(255))
    role = Column(String(50))
    firebase_uid = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    

    def __repr__(self):
        return f"{self.id} {self.phone}"   

    # @property
    # def about_me_list(self):
    #     if self.about_me is None:
    #         return []
    #     # Memecah deskripsi berdasarkan paragraf yang dipisahkan oleh baris baru
    #     d_list = re.split(r"\n+", self.about_me)
    #     return [d.strip() for d in d_list if d.strip()]  # Menghapus spasi kosong di awal/akhir paragraf
    
    # @property
    # def about_me_list(self):
    #     if self.about_me is None:
    #         return []
    #     d_list = re.split("\\s{4,}", self.about_me)
    #     return [d for d in d_list if len(d) != 0]

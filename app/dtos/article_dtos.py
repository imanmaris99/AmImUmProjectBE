from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# DTO untuk membuat artikel baru
class ArticleCreateDTO(BaseModel):
    title: Optional[str]
    img: Optional[str] = None
    description: str = Field(default="this is good news")

    
class ArticleIdToUpdateDto(BaseModel):
    article_id:int

# DTO untuk memperbarui informasi artikel
class ArticleDataUpdateDTO(BaseModel):
    title: Optional[str]
    description: Optional[str] = None

class ArticleInfoUpdateResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Updated Info about some article has been success")
    data: ArticleDataUpdateDTO

# DTO untuk respon artikel
class ArticleResponseDTO(BaseModel):
    id: int
    display_id: int
    title: str
    img: Optional[str] = None
    description_list: list[str]  # Properti untuk deskripsi yang dipisah menjadi list
    created_at: datetime

class GetAllArticleDTO(BaseModel):
    display_id: Optional[int] = None
    title: str
    img: Optional[str] = None
    description_list: list[str]  # Properti untuk deskripsi yang dipisah menjadi list


class DeleteArticleDto(BaseModel):
    article_id:int

class InfoDeleteArticleDto(BaseModel):
    article_id: int
    title: str

class DeleteArticleResponseDto(BaseModel):
    status_code: int = Field(default=200)
    message: str = Field(default="Your article has been deleted")
    data: InfoDeleteArticleDto
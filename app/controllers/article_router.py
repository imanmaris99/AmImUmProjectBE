# routes/article_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from app.dtos.article_dtos import ArticleCreateDTO, ArticleIdToUpdateDto, ArticleDataUpdateDTO, ArticleInfoUpdateResponseDto, ArticleResponseDTO, ArticleCreateResponseDto, GetAllArticleDTO, DeleteArticleDto, DeleteArticleResponseDto
from app.services import article_services
from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/articles",
    tags=["Articles"]
)

@router.post(
        "/create", 
        response_model=ArticleCreateResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)],
        responses={
            status.HTTP_201_CREATED: {
                "description": "Artikel berhasil dibuat",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 201,
                            "message": "Successfully created new article",
                            "data": {
                                "id": 1,
                                "title": "Herbal Remedies for Everyday Health",
                                "content": "Artikel ini membahas manfaat herbal...",
                                "author": "Admin",
                                "created_at": "2024-10-31T10:00:00",
                            }
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Token tidak valid atau pengguna tidak memiliki akses",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Token tidak valid atau pengguna tidak memiliki akses."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat membuat artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat membuat artikel."
                        }
                    }
                }
            }
        },
        summary="Create a new article"
    )
def create_article(
    article_create_dto: ArticleCreateDTO, 
    db: Session = Depends(get_db),
):
    """
    # Buat Artikel Baru #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk membuat artikel baru.
    
    **Parameter:**
    - **article_create_dto** (ArticleCreateDTO): Data artikel baru yang akan dibuat.

    **Return:**
    - **201 Created**: Artikel berhasil dibuat.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **500 Internal Server Error**: Kesalahan server saat membuat artikel.
    """
    result = article_services.create_article(db, article_create_dto)
    
    if result.error:
        raise result.error
    
    return result.data

@router.get(
        "/all", 
        response_model=List[GetAllArticleDTO],
        status_code=status.HTTP_200_OK,
        responses={
        status.HTTP_200_OK: {
            "description": "Daftar semua artikel berhasil diambil",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "display_id": 1,
                            "title": "Manfaat Herbal untuk Kesehatan",
                            "img": "https://example.com/image.jpg",
                            "description_list": [
                                "Herbal ini dapat meningkatkan kesehatan jantung.",
                                "Membantu meningkatkan sistem kekebalan tubuh."
                            ]
                        },
                        {
                            "display_id": 2,
                            "title": "Herbal Populer dalam Pengobatan Modern",
                            "img": "https://example.com/image2.jpg",
                            "description_list": [
                                "Herbal ini digunakan dalam pengobatan tradisional.",
                                "Bermanfaat untuk kesehatan mental dan fisik."
                            ]
                        }
                    ]
                }
            }
        },
            status.HTTP_409_CONFLICT: {
                "description": "Terjadi konflik saat mengambil daftar artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Terjadi konflik saat mengambil daftar artikel."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat mengambil daftar artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat mengambil daftar artikel."
                        }
                    }
                }
            }
        },
        summary="Retrieve a list of all articles"
    )
def read_articles(
    db: Session = Depends(get_db)
):
    """
    # Dapatkan Daftar Semua Artikel #

    Endpoint ini digunakan untuk mendapatkan semua artikel yang tersedia dalam database.
    
    **Return:**
    - **200 OK**: Daftar semua artikel berhasil diambil.
    - **409 Conflict**: Terjadi konflik saat mengambil daftar artikel.
    - **500 Internal Server Error**: Kesalahan server saat mengambil daftar artikel.
    """
    result = article_services.get_articles(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.put(
        "/update/{article_id}", 
        response_model=ArticleInfoUpdateResponseDto,
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(jwt_service.admin_access_required)],
        responses={
            status.HTTP_200_OK: {
                "description": "Artikel berhasil diperbarui",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Updated Info about some article has been success",
                            "data": {
                                "title": "Updated Article Title",
                                "description": "This is the updated description of the article."
                            }
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Token tidak valid atau pengguna tidak terautentikasi",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Token tidak valid atau pengguna tidak memiliki akses."
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Artikel tidak ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Artikel dengan ID ini tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_409_CONFLICT: {
                "description": "Terjadi konflik saat memperbarui artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Konflik saat memperbarui data artikel."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat memperbarui artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat memperbarui artikel."
                        }
                    }
                }
            }
        },
        summary="Update an article"
    )
def update_article(
    article_id_update: ArticleIdToUpdateDto, 
    article_update_dto: ArticleDataUpdateDTO,
    db: Session = Depends(get_db)
):
    """
    # Update Artikel #

    Endpoint ini digunakan untuk memperbarui artikel tertentu berdasarkan ID.
    
    **Parameter:**
    - **article_id_update** (ArticleIdToUpdateDto): ID dari artikel yang ingin diperbarui.
    - **article_update_dto** (ArticleDataUpdateDTO): Data artikel yang diperbarui.
    
    **Return:**
    - **200 OK**: Artikel berhasil diperbarui.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak terautentikasi.
    - **404 Not Found**: Artikel tidak ditemukan.
    - **409 Conflict**: Terjadi konflik saat memperbarui artikel.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui artikel.
    """
    result = article_services.update_article(db, article_id_update, article_update_dto)
    
    if result.error:
        raise result.error
    
    return result.data

@router.delete(
        "/delete/{article_id}", 
        response_model= DeleteArticleResponseDto,
        dependencies=[Depends(jwt_service.admin_access_required)],
        status_code=status.HTTP_200_OK,
        responses={
            status.HTTP_200_OK: {
                "description": "Artikel berhasil dihapus",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Your article has been deleted",
                            "data": {
                                "article_id": 1,
                                "title": "Manfaat Herbal untuk Kesehatan"
                            }
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Token tidak valid atau pengguna tidak terautentikasi",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Token tidak valid atau pengguna tidak memiliki akses."
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Artikel tidak ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Artikel dengan ID ini tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_409_CONFLICT: {
                "description": "Terjadi konflik saat menghapus artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Terjadi konflik saat menghapus artikel."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat menghapus artikel",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat menghapus artikel."
                        }
                    }
                }
            }
        },
        summary="Delete an article by its ID"
    )
def delete_article(
    article_data: DeleteArticleDto, 
    db: Session = Depends(get_db)
):
    """
    # Hapus Artikel Berdasarkan ID #

    Endpoint ini digunakan untuk menghapus artikel tertentu berdasarkan ID yang diberikan.
    
    **Parameter:**
    - **article_id** (int): ID dari artikel yang ingin dihapus.

    **Return:**
    - **200 OK**: Artikel berhasil dihapus.
    - **404 Not Found**: Artikel dengan ID ini tidak ditemukan.
    - **409 Conflict**: Terjadi konflik saat menghapus artikel.
    - **500 Internal Server Error**: Kesalahan server saat menghapus artikel.
    """
    result = article_services.delete_article(
        db, 
        article_data=article_data
    )

    if result.error:
        raise result.error
    
    return result.unwrap()
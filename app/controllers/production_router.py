from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import production_dtos
from app.services import production_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/brand",
    tags=["Brand Production"]
)

@router.post(
        "/create", 
        response_model=production_dtos.ProductionCreateResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)],
        responses={
            status.HTTP_201_CREATED: {
                "description": "Data produksi berhasil dibuat",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 201,
                            "message": "Create manufactured by some Company has been success",
                            "data": {
                                "name": "string",
                                "herbal_category_id": 1,
                                "description": "string"
                            }
                        }
                    }
                }
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Permintaan tidak valid karena kesalahan input",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 400,
                            "error": "Bad Request",
                            "message": "Invalid data provided"
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Pengguna tidak memiliki hak akses sebagai admin",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "User is not authorized to create production data."
                        }
                    }
                }
            },
            status.HTTP_409_CONFLICT: {
                "description": "Konflik terjadi saat membuat data produksi",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Data conflict occurred while creating production."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat membuat data produksi",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Unexpected error occurred while creating production."
                        }
                    }
                }
            }
        },
        summary="Create a New Production"
    )
def create_productions(
    production_create: production_dtos.ProductionCreateDto, 
    jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
    db: Session = Depends(get_db),
):
    """
    # Buat Data Baru untuk Brand Pembuat Produk #

    Endpoint ini digunakan untuk membuat data produksi baru oleh pengguna yang memiliki akses sebagai admin.

    **Parameter:**
    - **production_create** (ProductionCreateDto): Data produksi yang akan dibuat, mencakup nama, kategori herbal, dan deskripsi.
    - **jwt_token**: Token JWT yang berisi informasi pengguna, diambil dari `Depends(jwt_service.get_jwt_pyload)`.
    - **db** (Session): Koneksi ke database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **201 Created**: Data produksi berhasil dibuat.
    - **400 Bad Request**: Permintaan tidak valid karena data input yang salah.
    - **403 Forbidden**: Pengguna tidak memiliki hak akses sebagai admin.
    - **409 Conflict**: Konflik terjadi saat membuat data produksi baru.
    - **500 Internal Server Error**: Kesalahan tak terduga di server saat membuat data produksi.
    """
        
    result = production_services.create_production(
        db, 
        production_create,
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
        "/all", 
        response_model=production_dtos.AllListProductionResponseDto,
        status_code=status.HTTP_200_OK,
        responses={
                status.HTTP_409_CONFLICT: {
                    "description": "Konflik saat mengambil daftar perusahaan produksi",
                    "content": {
                        "application/json": {
                            "example": {
                                "status_code": 409,
                                "error": "Conflict",
                                "message": "Konflik terjadi saat mencoba mengambil data perusahaan produksi."
                            }
                        }
                    }
                },
                status.HTTP_500_INTERNAL_SERVER_ERROR: {
                    "description": "Kesalahan server saat mengambil daftar perusahaan produksi",
                    "content": {
                        "application/json": {
                            "example": {
                                "status_code": 500,
                                "error": "Internal Server Error",
                                "message": "Kesalahan tak terduga saat mengambil data perusahaan produksi."
                            }
                        }
                    }
                }
            },
        summary="Get All Productions Company"
    )
def read_productions(   
    db: Session = Depends(get_db)
):
    """
    # Menampilkan Semua List dari Perusahaan Produksi #
    
    Endpoint ini digunakan untuk mengambil daftar semua perusahaan produksi yang ada di database.
    
    **Parameter:**
    - **db** (Session): Koneksi ke database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **200 OK**: Daftar perusahaan produksi yang berhasil diambil.
    - **409 Conflict**: Konflik terjadi saat mencoba mengambil data perusahaan produksi.
    - **500 Internal Server Error**: Kesalahan tak terduga di server saat mengambil data.
   
    """
    result = production_services.get_all_productions(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/loader",
    response_model=production_dtos.ArticleListScrollResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Daftar produk berhasil diambil dengan format respons infinite scrolling",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Product A",
                                "photo_url": "http://example.com/product_a.jpg",
                                "description_list": "Brief description of Product A",
                                "category": "Category A",
                                "created_at": "2023-01-01T12:00:00Z"
                            },
                            {
                                "id": 2,
                                "name": "Product B",
                                "photo_url": "http://example.com/product_b.jpg",
                                "description_list": "Brief description of Product B",
                                "category": "Category B",
                                "created_at": "2023-01-02T12:00:00Z"
                            }
                        ],
                        "remaining_records": 94,
                        "has_more": True
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Data produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "No information about productions found."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Konflik saat mengambil data produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Database conflict occurred while fetching data."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while fetching data."
                    }
                }
            }
        }
    },
    summary="Fetch a paginated list of products"
)
def get_productions(
    skip: int = 0,               # Posisi awal data untuk pagination
    limit: int = 8,              # Jumlah data yang akan ditampilkan per halaman
    db: Session = Depends(get_db)
):
    """
    # Menampilkan List Brand dengan Pagination #

    Endpoint ini memungkinkan pengguna untuk Mengambil daftar item produksi dengan menggunakan paginasi.

    **Parameter:**
    - **skip** (int, opsional): Jumlah item yang dilewati sebelum memulai pengambilan data. Default adalah 0.
    - **limit** (int, opsional): Jumlah maksimum item yang akan dikembalikan dalam respons. Default adalah 6.
    
    **Return:**
    - **200 OK**: Daftar item produksi beserta metadata paginasi (remaining records, `has_more`).
    - **404 Not Found**: Jika tidak ada item produksi yang ditemukan.
    - **409 Conflict**: Jika terjadi kesalahan pada database.
    - **500 Internal Server Error**: Jika terjadi kesalahan yang tidak terduga.

    """
    result = production_services.get_infinite_scrolling(
        db, skip=skip, limit=limit
    )

    if result.error:
        raise result.error  
    
    return result.unwrap()


@router.get(
    "/promo", 
    response_model=production_dtos.AllProductionPromoResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Data promosi tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tidak ada data promosi yang ditemukan."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Konflik saat mengambil data promosi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Konflik terjadi saat mencoba mengambil data promosi."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil data promosi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat mengambil data promosi."
                    }
                }
            }
        }
    },
    summary="Get All Promotions of some Brand"
)
def read_promo(   
    db: Session = Depends(get_db)
):
    """
    # Ambil Semua Promosi #
    
    Endpoint ini digunakan untuk mengambil daftar semua promosi khusus yang ditawarkan pada produk tertentu.

    **Parameter:**
    - **db** (Session): Koneksi ke database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **200 OK**: Daftar promosi berhasil diambil.
    - **404 Not Found**: Tidak ada data promosi yang ditemukan.
    - **409 Conflict**: Konflik terjadi saat mencoba mengambil data promosi.
    - **500 Internal Server Error**: Kesalahan tak terduga di server saat mengambil data.
    
    """
    result = production_services.get_all_promo(db)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
    "/detail/{production_id}", 
    response_model=production_dtos.ProductionDetailResponseDto,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Detail produksi berhasil ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Info about Production or brand details successfully retrieved",
                        "data": {
                            "id": 0,
                            "name": "string",
                            "photo_url": "string",
                            "description_list": [
                                "string"
                            ],
                            "category": "string",
                            "total_product": 0,
                            "created_at": "2024-11-02T08:43:46.577Z"
                        }
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produksi tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Production with the specified ID was not found."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Konflik saat mengambil detail produksi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "A conflict occurred while retrieving production details."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil detail produksi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred while retrieving production details."
                    }
                }
            }
        }
    },
    summary="Get Production Details"
)
def get_production_detail(
    production_id: int, 
    db: Session = Depends(get_db)
):
    """
    # Dapatkan Detail Produksi #

    Endpoint ini mengambil informasi detail dari sebuah produksi berdasarkan ID yang diberikan.

    **Parameter:**
    - **production_id** (int): ID dari produksi yang ingin dilihat detailnya.
    - **db** (Session): Koneksi database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **200 OK**: Detail produksi berhasil ditemukan.
    - **404 Not Found**: Produksi dengan ID yang diminta tidak ditemukan.
    - **409 Conflict**: Konflik terjadi saat mengambil detail produksi.
    - **500 Internal Server Error**: Kesalahan tak terduga di server saat mengambil detail produksi.
    
    """
    result = production_services.detail_production(
        db, 
        production_id)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.put(
    "/{production_id}",
    response_model=production_dtos.ProductionInfoUpdateResponseDto,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(jwt_service.admin_access_required)],
    responses={
        status.HTTP_200_OK: {
            "description": "Informasi produksi berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Updated Info about some company production has been success",
                        "data": {
                            "name": "string",
                            "description": "string"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Permintaan tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang diberikan tidak valid atau tidak lengkap."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Pengguna tidak memiliki hak akses",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Pengguna tidak diizinkan untuk memperbarui informasi produksi ini."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produksi tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Produksi dengan ID yang diminta tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Konflik saat memperbarui informasi produksi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Konflik terjadi saat memperbarui data produksi."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui informasi produksi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui informasi produksi."
                    }
                }
            }
        }
    },
    summary="Update Production Company Information",
)
def update_info_company(
    company_id: production_dtos.ProductionIdToUpdateDto, 
    production_update: production_dtos.ProductionInfoUpdateDTO,
    db: Session = Depends(get_db)
):
    """
    # Perbarui Informasi Produksi #

    Endpoint ini digunakan untuk memperbarui informasi produksi berdasarkan ID produksi.

    **Parameter:**
    - **production_id** (int): ID dari produksi yang ingin diperbarui.
    - **production_update** (ProductionInfoUpdateDTO): Data baru untuk produksi tersebut.
    - **jwt_token**: Token JWT yang berisi informasi pengguna, diambil dari `Depends(jwt_service.get_jwt_pyload)`.
    - **db** (Session): Koneksi database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **200 OK**: Informasi produksi berhasil diperbarui.
    - **400 Bad Request**: Data yang diberikan tidak valid atau tidak lengkap.
    - **403 Forbidden**: Pengguna tidak memiliki hak akses untuk memperbarui informasi produksi ini.
    - **404 Not Found**: Produksi dengan ID yang diminta tidak ditemukan.
    - **409 Conflict**: Konflik terjadi saat memperbarui data produksi.
    - **500 Internal Server Error**: Kesalahan tak terduga di server saat memperbarui informasi produksi.
    
    """
    result = production_services.edit_production(
        db=db, 
        company_id=company_id, 
        production_update=production_update 
    )

    # Tangani error jika ada
    if result.error:
        raise result.error

    return result.unwrap()

@router.put(
        "/logo/{production_id}", 
        response_model=production_dtos.PostLogoCompanyResponseDto,
        status_code=status.HTTP_200_OK,
        dependencies=[Depends(jwt_service.admin_access_required)],
        responses={
            status.HTTP_200_OK: {
                "description": "Logo perusahaan berhasil diperbarui",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Post your Company-Logo has been success",
                            "data": {
                                "photo_url": "string"
                            }
                        }
                    }
                }
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Permintaan tidak valid",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 400,
                            "error": "Bad Request",
                            "message": "File logo tidak valid atau tidak ada."
                        }
                    }
                }
            },
            status.HTTP_403_FORBIDDEN: {
                "description": "Pengguna tidak memiliki hak akses",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 403,
                            "error": "Forbidden",
                            "message": "Pengguna tidak diizinkan untuk memperbarui logo perusahaan ini."
                        }
                    }
                }
            },
            status.HTTP_404_NOT_FOUND: {
                "description": "Produksi tidak ditemukan",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 404,
                            "error": "Not Found",
                            "message": "Produksi dengan ID yang diminta tidak ditemukan."
                        }
                    }
                }
            },
            status.HTTP_409_CONFLICT: {
                "description": "Konflik saat memperbarui logo",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 409,
                            "error": "Conflict",
                            "message": "Konflik terjadi saat memperbarui logo perusahaan."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Kesalahan server saat memperbarui logo",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "Kesalahan tak terduga saat memperbarui logo perusahaan."
                        }
                    }
                }
            }
        },
    summary="Update Company Logo"
)
async def update_logo(
        production_id: int,
        file: UploadFile = None,  # Jika opsional, tetap `None`; jika wajib, gunakan `File(...)`
        jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
        db: Session = Depends(get_db)
):
    """
    # Update Logo Perusahaan #

    Endpoint ini digunakan untuk mengunggah dan memperbarui logo perusahaan produsen.

    **Parameter:**
    - **production_id** (int): ID dari produksi yang ingin diperbarui logonya.
    - **file** (UploadFile): File logo baru untuk perusahaan. Jika tidak ada, logo tidak akan diperbarui.
    - **jwt_token**: Token JWT yang berisi ID pengguna yang sudah terautentikasi.
    - **db** (Session): Koneksi database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **200 OK**: Logo berhasil diperbarui.
    - **400 Bad Request**: File tidak valid atau tidak tersedia.
    - **403 Forbidden**: Pengguna tidak memiliki hak akses.
    - **404 Not Found**: Produksi dengan ID yang diminta tidak ditemukan.
    - **409 Conflict**: Konflik saat memperbarui data.
    - **500 Internal Server Error**: Kesalahan tak terduga di server.
    
    """
    result = await production_services.post_logo(
        db=db, 
        production_id=production_id,
        user_id=jwt_token.id,  # Mengambil ID dari payload JWT
        file=file
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.delete(
    "/delete/{production_id}", 
    response_model= production_dtos.DeleteProdutionResponseDto,
    dependencies=[Depends(jwt_service.admin_access_required)],
    responses={
        status.HTTP_200_OK: {
            "description": "Perusahaan berhasil dihapus",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Info about company some product has been deleted",
                        "data": {
                            "id": 0,
                            "name": "string"
                        }
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Pengguna tidak memiliki hak akses untuk menghapus",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbidden",
                        "message": "Pengguna tidak memiliki izin untuk menghapus info dari perusahaan produsen ini."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Produksi tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Produksi dengan ID yang diminta tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Konflik saat menghapus produksi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Konflik terjadi saat mencoba menghapus produksi ini."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat menghapus produksi",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat menghapus produksi."
                    }
                }
            }
        }
    },
    summary="Delete a Company Production"
)
def delete_company(
    deleted_data: production_dtos.ProductionIdToUpdateDto, 
    db: Session = Depends(get_db)
):
    """
    # Delete Production Company #

    Endpoint ini menghapus produksi tertentu berdasarkan `production_id` yang diberikan.

    **Parameter:**
    - **production_id** (int): ID dari produksi yang ingin dihapus.
    - **jwt_token**: Token JWT yang berisi ID pengguna yang sudah terautentikasi.
    - **db** (Session): Koneksi database yang diambil dari `Depends(get_db)`.

    **Return:**
    - **200 OK**: Berhasil menghapus produksi.
    - **403 Forbidden**: Pengguna tidak memiliki izin untuk menghapus.
    - **404 Not Found**: Produksi tidak ditemukan.
    - **409 Conflict**: Konflik saat menghapus.
    - **500 Internal Server Error**: Kesalahan tak terduga.
    
    """
    result = production_services.delete_production(
        db, 
        deleted_data=deleted_data
    )

    if result.error:
        raise result.error
    
    return result.unwrap()
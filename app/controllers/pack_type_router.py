from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import pack_type_dtos
from app.services import pack_type_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/type",
    tags=["Type/ Variant"]
)

@router.post(
    "/create", 
    response_model=pack_type_dtos.PackTypeResponseCreateDto,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(jwt_service.admin_access_required)],
    responses={
        status.HTTP_201_CREATED: {
            "description": "Tipe produk berhasil dibuat",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Successfully created pack type",
                        "data": {
                            "id": 1,
                            "name": "Sachet",
                            "min_amount": 1,
                            "variant": "Herbal Powder",
                            "expiration": "2024-12-31",
                            "stock": 100,
                            "discount": 5.0,
                            "created_by": 1,
                            "created_at": "2024-10-31T10:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Data yang dikirim tidak valid atau tidak lengkap",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang dikirim tidak lengkap atau tidak valid."
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
            "description": "Kesalahan server saat membuat tipe produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat membuat tipe produk."
                    }
                }
            }
        }
    },
    summary="Create a new product pack type"
)
def create_types(
    type_create: pack_type_dtos.PackTypeCreateDto, 
    jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
    db: Session = Depends(get_db),
):
    """
    # Buat Tipe Produk Baru #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk membuat tipe produk baru.
    
    **Parameter:**
    - **type_create** (PackTypeCreateDto): Data tipe produk baru yang akan dibuat.
    - **jwt_token** (TokenPayLoad): Payload token JWT yang berisi informasi pengguna.
    
    **Return:**
    - **201 Created**: Tipe produk berhasil dibuat.
    - **400 Bad Request**: Data yang dikirim tidak lengkap atau tidak valid.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **500 Internal Server Error**: Kesalahan server saat membuat tipe produk.
    
    """
    result = pack_type_services.create_type(
        db, 
        type_create,
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/all", 
    response_model=List[pack_type_dtos.VariantProductDto],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Daftar tipe produk berhasil diambil",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Sachet",
                            "min_amount": 1,
                            "variant": "Herbal Powder",
                            "expiration": "2024-12-31",
                            "stock": 100,
                            "discount": 5.0,
                            "created_by": 1,
                            "created_at": "2024-10-31T10:00:00"
                        },
                        {
                            "id": 2,
                            "name": "Gram",
                            "min_amount": 5,
                            "variant": "Organic Tea",
                            "expiration": "2024-12-31",
                            "stock": 200,
                            "discount": 10.0,
                            "created_by": 2,
                            "created_at": "2024-10-31T10:00:00"
                        }
                    ]
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat mengambil tipe produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat mengambil daftar tipe produk."
                    }
                }
            }
        }
    },
    summary="Get all product types"
)
def read_types(   
    db: Session = Depends(get_db)
):
    """
    # Ambil Daftar Tipe Produk #

    Endpoint ini mengembalikan daftar semua tipe produk yang tersedia dalam sistem.
    
    **Return:**
    - **200 OK**: Daftar tipe produk berhasil diambil.
    - **500 Internal Server Error**: Kesalahan server saat mengambil daftar tipe produk.
    
    """
    result = pack_type_services.all_types(db)
    return result.unwrap()

@router.put(
    "/{type_id}",
    response_model=pack_type_dtos.PackTypeEditInfoResponseDto,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(jwt_service.admin_access_required)],
    responses={
        status.HTTP_200_OK: {
            "description": "Tipe produk berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Pack type successfully updated",
                        "data": {
                            "id": 1,
                            "name": "Sachet",
                            "min_amount": 2,
                            "variant": "Herbal Powder",
                            "expiration": "2024-12-31",
                            "stock": 120,
                            "discount": 10.0,
                            "updated_at": "2024-10-31T12:00:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Data yang dikirim tidak valid atau tidak lengkap",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Data yang dikirim tidak lengkap atau tidak valid."
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
        status.HTTP_404_NOT_FOUND: {
            "description": "Tipe produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tipe produk dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui tipe produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui tipe produk."
                    }
                }
            }
        }
    },
    summary="Update the stock of a product type"
)
def update_stock(
    type_id_update: pack_type_dtos.TypeIdToUpdateDto, 
    type_update_dto: pack_type_dtos.PackTypeEditInfoDto,
    db: Session = Depends(get_db)
):
    """
    # Perbarui Stok Tipe Produk #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk memperbarui stok dan informasi lainnya dari tipe produk yang ada.
    
    **Parameter:**
    - **type_id_update** (TypeIdToUpdateDto): ID tipe produk yang akan diperbarui.
    - **type_update_dto** (PackTypeEditInfoDto): Data yang akan diperbarui untuk tipe produk.
    
    **Return:**
    - **200 OK**: Tipe produk berhasil diperbarui.
    - **400 Bad Request**: Data yang dikirim tidak lengkap atau tidak valid.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **404 Not Found**: Tipe produk dengan ID yang diberikan tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui tipe produk.
    
    """
    result = pack_type_services.update_stock(
        db=db, 
        type_id_update=type_id_update, 
        type_update=type_update_dto  
    )

    # Tangani error jika ada
    if result.error:
        raise result.error

    return result.unwrap()

@router.put(
    "/image/{type_id}", 
    response_model=pack_type_dtos.EditPhotoProductResponseDto,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(jwt_service.admin_access_required)],
    responses={
        status.HTTP_201_CREATED: {
            "description": "Foto produk berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "Pack type photo successfully updated",
                        "data": {
                            "type_id": 1,
                            "photo_url": "https://example.com/images/new-photo.jpg",
                            "updated_at": "2024-10-31T12:30:00"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "File yang dikirim tidak valid atau tidak dapat diunggah",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "File yang dikirim tidak valid atau tidak dapat diunggah."
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
        status.HTTP_404_NOT_FOUND: {
            "description": "Tipe produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tipe produk dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat memperbarui foto produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat memperbarui foto produk."
                    }
                }
            }
        }
    },
    summary="Update the logo of a product type"
)
async def update_logo(
        type_id: int,
        file: UploadFile = None,  # Jika opsional, tetap `None`; jika wajib, gunakan `File(...)`
        jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
        db: Session = Depends(get_db)
):
    """
    # Perbarui Foto Tipe Produk #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk memperbarui foto dari tipe produk tertentu.
    
    **Parameter:**
    - **type_id** (int): ID tipe produk yang foto-nya akan diperbarui.
    - **file** (UploadFile): File gambar yang akan diunggah.
    
    **Return:**
    - **201 Created**: Foto tipe produk berhasil diperbarui.
    - **400 Bad Request**: File yang dikirim tidak valid atau tidak dapat diunggah.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **404 Not Found**: Tipe produk dengan ID yang diberikan tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan server saat memperbarui foto produk.
    
    """
    result = await pack_type_services.post_photo(
        db=db, 
        type_id=type_id,
        user_id=jwt_token.id,  # Mengambil ID dari payload JWT
        file=file
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.delete(
    "/delete/{type_id}", 
    response_model= pack_type_dtos.DeletePackTypeResponseDto,
    dependencies=[Depends(jwt_service.admin_access_required)],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Tipe produk berhasil dihapus",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 200,
                        "message": "Pack type successfully deleted",
                        "data": {
                            "type_id": 1,
                            "message": "Pack type with ID 1 has been successfully deleted."
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
        status.HTTP_404_NOT_FOUND: {
            "description": "Tipe produk tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Tipe produk dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server saat menghapus tipe produk",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Kesalahan tak terduga saat menghapus tipe produk."
                    }
                }
            }
        }
    },
    summary="Delete a product type"
)
def delete_variant(
    variant_data: pack_type_dtos.DeletePackTypeDto, 
    db: Session = Depends(get_db)
):
    """
    # Hapus Tipe Produk #

    Endpoint ini memungkinkan pengguna dengan akses admin untuk menghapus tipe produk berdasarkan ID-nya.
    
    **Parameter:**
    - **type_id** (int): ID tipe produk yang akan dihapus.
    
    **Return:**
    - **200 OK**: Tipe produk berhasil dihapus.
    - **403 Forbidden**: Token tidak valid atau pengguna tidak memiliki akses.
    - **404 Not Found**: Tipe produk dengan ID yang diberikan tidak ditemukan.
    - **500 Internal Server Error**: Kesalahan server saat menghapus tipe produk.
    
    """
    result = pack_type_services.delete_type(
        db, 
        variant_data=variant_data)
    
    if result.error:
        raise result.error
    
    return result.unwrap()
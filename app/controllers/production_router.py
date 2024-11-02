from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import production_dtos
from app.services import production_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/production",
    tags=["Production-by"]
)

@router.post(
        "/create", 
        response_model=production_dtos.ProductionCreateResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def create_productions(
    production_create: production_dtos.ProductionCreateDto, 
    jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
    db: Session = Depends(get_db),
):
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
        response_model=List[production_dtos.AllProductionsDto],
        summary="Get All Productions Company",
        description="Retrieve a list of productions companies."

    )
def read_productions(   
    db: Session = Depends(get_db)
):
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
    limit: int = 6,              # Jumlah data yang akan ditampilkan per halaman
    db: Session = Depends(get_db)
):
    """
    # Menampilkan List Brand dengan Pagination #

    Endpoint ini memungkinkan pengguna untuk Mengambil daftar item produksi dengan menggunakan paginasi.

    **Parameter**:
    - **skip** (int, opsional): Jumlah item yang dilewati sebelum memulai pengambilan data. Default adalah 0.
    - **limit** (int, opsional): Jumlah maksimum item yang akan dikembalikan dalam respons. Default adalah 6.
    
    **Mengembalikan**:
    - **200 OK**: Daftar item produksi beserta metadata paginasi (remaining records, `has_more`).
    - **404 Not Found**: Jika tidak ada item produksi yang ditemukan.
    - **409 Conflict**: Jika terjadi kesalahan pada database.
    - **500 Internal Server Error**: Jika terjadi kesalahan yang tidak terduga.

    """
    result = production_services.get_infinite_scrolling(
        db, skip=skip, limit=limit
    )

    if result.error:
        raise result.error  # Raise the error if there is one

    return result.unwrap()


@router.get(
    "/promo", 
    response_model=List[production_dtos.AllProductionPromoDto],
    summary="Get All Promotions",
    description="Retrieve a list of productions with special promotions."
)
def read_promo(   
    db: Session = Depends(get_db)
):
    result = production_services.get_all_promo(db)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
        "/detail/{production_id}", 
        response_model=production_dtos.ProductionDetailResponseDto
    )
def get_production_detail(
    production_id: int, 
    db: Session = Depends(get_db)):


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
    dependencies=[Depends(jwt_service.admin_access_required)]  # Pastikan Anda memiliki dependency untuk akses admin
)
def update_info_company(
    company_id: production_dtos.ProductionIdToUpdateDto, 
    production_update: production_dtos.ProductionInfoUpdateDTO,
    db: Session = Depends(get_db)
):
    # Panggil service untuk memperbarui stok
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
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
async def update_logo(
        production_id: int,
        file: UploadFile = None,  # Jika opsional, tetap `None`; jika wajib, gunakan `File(...)`
        jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
        db: Session = Depends(get_db)
):
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
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def delete_company(
    deleted_data: production_dtos.ProductionIdToUpdateDto, 
    db: Session = Depends(get_db)
):
    result = production_services.delete_production(
        db, 
        deleted_data=deleted_data
    )

    if result.error:
        raise result.error
    
    return result.unwrap()
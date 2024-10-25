from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import product_dtos
from app.services import product_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/product",
    tags=["Product"]
)

@router.post(
        "/", 
        response_model=product_dtos.ProductResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def create_product(
    create_product: product_dtos.ProductCreateDTO, 
    db: Session = Depends(get_db),
):
    result = product_services.create_product(
        db, 
        create_product
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
        "/", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def read_all_products(   
    db: Session = Depends(get_db)
):
    result = product_services.all_product(db)

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
        "/discount", 
        response_model=List[product_dtos.AllProductInfoDTO]
    )
def read_all_products_with_discount(   
    db: Session = Depends(get_db)
):
    result = product_services.all_product_with_discount(db)

    if result.error:
        raise result.error
    
    return result.unwrap()


@router.get(
    "/production/{production_id}", 
    response_model=List[product_dtos.AllProductInfoDTO]
)
def read_all_products_by_id_production(
    production_id: int,  # Ambil production_id dari path
    db: Session = Depends(get_db)
):
    # Langsung kirim production_id ke service tanpa DTO
    result = product_services.all_product_by_id_production(
        db=db,
        production_id=production_id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
    "/discount/{production_id}", 
    response_model=List[product_dtos.AllProductInfoDTO]
)
def read_all_products_discount_by_id_production(
    production_id: int,  # Ambil production_id dari path
    db: Session = Depends(get_db)
):
    # Langsung kirim production_id ke service tanpa DTO
    result = product_services.all_discount_by_id_production(
        db=db,
        production_id=production_id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


# @router.put(
#     "/{type_id}",
#     response_model=pack_type_dtos.PackTypeEditInfoResponseDto,
#     status_code=status.HTTP_200_OK,
#     dependencies=[Depends(jwt_service.admin_access_required)]  # Pastikan Anda memiliki dependency untuk akses admin
# )
# def update_stock(
#     type_id_update: pack_type_dtos.TypeIdToUpdateDto, 
#     type_update_dto: pack_type_dtos.PackTypeEditInfoDto,
#     db: Session = Depends(get_db)
# ):
#     # Panggil service untuk memperbarui stok
#     result = pack_type_services.update_stock(
#         db=db, 
#         type_id_update=type_id_update, 
#         type_update=type_update_dto  # Ganti type_update_dto sesuai parameter service
#     )

#     # Tangani error jika ada
#     if result.error:
#         raise result.error

#     return result.unwrap()

# @router.put(
#         "/image/{type_id}", 
#         response_model=pack_type_dtos.EditPhotoProductResponseDto,
#         status_code=status.HTTP_201_CREATED,
#         dependencies=[Depends(jwt_service.admin_access_required)]
#     )
# async def update_logo(
#         type_id: int,
#         file: UploadFile = None,  # Jika opsional, tetap `None`; jika wajib, gunakan `File(...)`
#         jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
#         db: Session = Depends(get_db)
# ):
#     result = await pack_type_services.post_photo(
#         db=db, 
#         type_id=type_id,
#         user_id=jwt_token.id,  # Mengambil ID dari payload JWT
#         file=file
#     )

#     if result.error:
#         raise result.error
    
#     return result.unwrap()


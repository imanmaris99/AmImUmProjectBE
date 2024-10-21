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
        "/", 
        response_model=pack_type_dtos.PackTypeResponseCreateDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
def create_types(
    type_create: pack_type_dtos.PackTypeCreateDto, 
    jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
    db: Session = Depends(get_db),
):
    result = pack_type_services.create_type(
        db, 
        type_create,
        jwt_token.id
    )

    if result.error:
        raise result.error
    
    return result.unwrap()

@router.get(
        "/", 
        response_model=List[pack_type_dtos.VariantProductDto]
    )
def read_types(   
    db: Session = Depends(get_db)
):
    result = pack_type_services.all_types(db)
    return result.unwrap()

@router.put(
    "/{type_id}",
    response_model=pack_type_dtos.PackTypeEditInfoResponseDto,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(jwt_service.admin_access_required)]  # Pastikan Anda memiliki dependency untuk akses admin
)
def update_stock(
    type_id_update: pack_type_dtos.TypeIdToUpdateDto, 
    type_update_dto: pack_type_dtos.PackTypeEditInfoDto,
    db: Session = Depends(get_db)
):
    # Panggil service untuk memperbarui stok
    result = pack_type_services.update_stock(
        db=db, 
        type_id_update=type_id_update, 
        type_update=type_update_dto  # Ganti type_update_dto sesuai parameter service
    )

    # Tangani error jika ada
    if result.error:
        raise result.error

    return result.unwrap()

@router.put(
        "/image/{type_id}", 
        response_model=pack_type_dtos.EditPhotoProductResponseDto,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(jwt_service.admin_access_required)]
    )
async def update_logo(
        type_id: int,
        file: UploadFile = None,  # Jika opsional, tetap `None`; jika wajib, gunakan `File(...)`
        jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
        db: Session = Depends(get_db)
):
    result = await pack_type_services.post_photo(
        db=db, 
        type_id=type_id,
        user_id=jwt_token.id,  # Mengambil ID dari payload JWT
        file=file
    )

    if result.error:
        raise result.error
    
    return result.unwrap()


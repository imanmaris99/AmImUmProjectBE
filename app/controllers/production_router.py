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
        "/", 
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
        "/", 
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
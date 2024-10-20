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

@router.get(
        "/", 
        response_model=List[production_dtos.AllProductionsDto]
    )
def read_productions(   
    db: Session = Depends(get_db)
):
    result = production_services.get_all_productions(db)
    return result.unwrap()
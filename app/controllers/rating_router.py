from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, UploadFile, status

from sqlalchemy.orm import Session
from typing import List, Annotated

from app.dtos import rating_dtos
from app.services import rating_services

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_dto, jwt_service

router = APIRouter(
    prefix="/rating",
    tags=["Rating of Product"]
)

@router.post(
        "/product/{product_id}", 
        response_model=rating_dtos.RatingResponseCreateDto,
        status_code=status.HTTP_201_CREATED
    )
def give_a_rate_of_product(
    product_id: UUID,
    create_rate: rating_dtos.RatingCreateDto, 
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db),
):
    # Panggil service untuk membuat rating
    result = rating_services.create_rating(
        db, 
        product_id,
        create_rate,
        jwt_token.id  # Menggunakan `id` dari JWT payload sebagai user_id
    )

    # Jika terjadi error, raise error-nya
    if result.error:
        raise result.error
    
    # Kembalikan hasil yang berhasil di-create
    return result.unwrap()



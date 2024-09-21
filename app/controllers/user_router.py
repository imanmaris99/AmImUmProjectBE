from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_service, jwt_dto

from app.services import user_services
from app.dtos import user_dtos


router = APIRouter(
    prefix="/user",
    tags=["User/ Customer"]
)

## == USER - REGISTER == ##
@router.post(
    "/register",
    response_model=user_dtos.UserCreateResponseDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "1",
                        "email": "user@example.com",
                        "username": "username",
                        "phone": "123456789",
                        "role": "customer",
                        "created_at": "2024-09-21T14:28:23.382Z",
                        "updated_at": "2024-09-21T14:28:23.382Z"
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "User already exists (email or username conflict)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email already exists. Please use a different email."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Server error while creating user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred while creating the user. Please try again later."
                    }
                }
            }
        }
    },
    summary="Register a new user"
)
def create_user(user: user_dtos.UserCreateDto, db: Session = Depends(get_db)):
    """
    # User/ Customer Register #
    This method is used to create a user
    """
    result = user_services.create_user(db, user)
    
    if result.error:
        raise result.error

    return result.unwrap()

## == USER - LOGIN == ##
@router.post(
    "/login",
    response_model=jwt_dto.AccessTokenDto,
    responses={
        status.HTTP_200_OK: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Your user account has been login successfully",
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
                        "token_type": "bearer"
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized. Incorrect email or password.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Password does not match."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with the provided email does not exist."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Server error during login",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "An error occurred during login. Please try again later."
                    }
                }
            }
        }
    },
    summary="User login"
)
def user_login(user: user_dtos.UserLoginPayloadDto, db: Session = Depends(get_db)):
    """
    # User/ Customer Login #
    This method is used for user login
    """
    
    user_optional = user_services.user_login(db=db, user=user)
    
    if user_optional.error:
        raise user_optional.error
    
    access_token = user_services.service_access_token(user_optional.data.id)
    
    return access_token
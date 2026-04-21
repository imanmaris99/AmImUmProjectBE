from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_service, jwt_dto

from app.services import user_services, order_services, payment_services
from app.services.admin_dashboard_summary import get_admin_dashboard_summary
from app.dtos import user_dtos, order_dtos, payment_dtos, admin_dashboard_dtos


router = APIRouter(
    prefix="/admin",
    tags=["User/ Admin"]
)

## == USER - REGISTER == ##
# @router.post(
#     "/register",
#     response_model=user_dtos.UserResponseDto,
#     status_code=status.HTTP_201_CREATED,
#     responses={
#         status.HTTP_201_CREATED: {
#             "description": "User successfully created",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 201,
#                         "message": "User successfully created",
#                         "data": {
#                             "id": "be65485e-167b-446b-9ce8-0dc11e87e06b",
#                             "email": "user@example.com",
#                             "firstname": "Budi",
#                             "lastname": "Pekerti",
#                             "gender": "man",
#                             "phone": "123456789",
#                             "role": "admin",
#                             "created_at": "2024-09-21T14:28:23.382Z",
#                             "updated_at": "2024-09-21T14:28:23.382Z"
#                         }
#                     }
#                 }
#             }
#         },
#         status.HTTP_400_BAD_REQUEST: {
#             "description": "User already exists (email or phone conflict)",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 400,
#                         "error": "Bad Request",
#                         "message": "Email already exists. Please use a different email."
#                     }
#                 }
#             }
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "description": "Server error while creating user",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 500,
#                         "error": "Database Error",
#                         "message": "An error occurred while creating the user. Please try again later."
#                     }
#                 }
#             }
#         }
#     },
#     summary="Register a new user as admin"
# )
# def create_admin(user: user_dtos.UserCreateDto, db: Session = Depends(get_db)):
#     """
#     # User as Admin Register #
#     This method is used to create a user
#     """
#     result = user_services.create_admin(db, user)
    
#     if result.error:
#         raise result.error  # Mengangkat kesalahan jika ada

#     return result.unwrap()  # Mengembalikan data dari service


## == USER - LOGIN == ##
@router.post(
    "/login",
    # response_model=jwt_dto.AccessTokenDto,
    response_model= user_dtos.UserLoginResponseDto,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Unauthorized. Incorrect email or password.",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 401,
                        "error": "UnAuthorized",
                        "message": "Password does not match."
                    }
                }
            }
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Your account is not active",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 403,
                        "error": "Forbiden Access",
                        "message": "Your account is not active. Please contact support."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "User with the provided email does not exist."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Server error during login",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Database Server Error",
                        "message": "An error occurred during login. Please try again later."
                    }
                }
            }
        }
    },
    summary="User as admin login"
)
def admin_login(user: user_dtos.UserLoginPayloadDto, db: Session = Depends(get_db)):
    """
    Admin Login
    This method is used for the user as admin to login
    """
    user_optional = user_services.user_login(db=db, user=user)
    
    if user_optional.error:
        raise user_optional.error

    user_data = user_optional.data

    return {
        "status_code": status.HTTP_200_OK,
        "message": "Your user account has been logged in successfully",
        "data":user_data
    }


@router.get(
    "/orders",
    response_model=order_dtos.GetOrderInfoResponseDto,
    summary="Admin get all orders",
    description="Mengambil seluruh order untuk kebutuhan dashboard admin. Mendukung pagination dasar dan filter status. Allowed status: pending, paid, processing, shipped, completed, cancelled, failed, capture, refund.",
)
def admin_get_all_orders(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    order_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    result = order_services.list_all_orders(
        db=db,
        skip=skip,
        limit=limit,
        status_filter=order_status,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/orders/{order_id}",
    response_model=order_dtos.GetOrderDetailResponseDto,
    summary="Admin get order detail",
    description="Mengambil detail satu order tertentu untuk admin tanpa pembatasan user pemilik order.",
)
def admin_get_order_detail(
    order_id: str,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = order_services.get_order_detail_admin(db=db, order_id=order_id)

    if result.error:
        raise result.error

    return result.unwrap()


@router.patch(
    "/orders/{order_id}/status",
    response_model=order_dtos.OrderInfoResponseDto,
    summary="Admin update order status",
    description="Memperbarui status order oleh admin. Allowed status: pending, paid, processing, shipped, completed, cancelled, failed, capture, refund.",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "status": "processing"
                    }
                }
            }
        }
    }
)
def admin_update_order_status(
    order_id: str,
    payload: order_dtos.AdminOrderStatusUpdateDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = order_services.update_order_status_admin(
        db=db,
        order_id=order_id,
        new_status=payload.status,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/payments",
    response_model=payment_dtos.AdminPaymentListResponseDto,
    summary="Admin get all payments",
    description="Mengambil seluruh payment untuk monitoring admin, dengan filter status transaksi dan pagination dasar. Allowed status: pending, settlement, expire, cancel, deny, refund, capture.",
)
def admin_get_all_payments(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    transaction_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    result = payment_services.list_all_payments(
        db=db,
        skip=skip,
        limit=limit,
        transaction_status_filter=transaction_status,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/payments/order/{order_id}",
    response_model=payment_dtos.AdminPaymentDetailResponseDto,
    summary="Admin get payment detail by order",
    description="Mengambil detail payment berdasarkan order_id untuk kebutuhan audit dan troubleshooting admin.",
)
def admin_get_payment_detail(
    order_id: str,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = payment_services.get_payment_detail_by_order_id(db=db, order_id=order_id)

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/users",
    response_model=user_dtos.AdminUserListResponseDto,
    summary="Admin get all users",
    description="Mengambil seluruh user untuk monitoring admin dan owner. Mendukung filter role, status aktif, dan pagination dasar.",
)
def admin_get_all_users(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    result = user_services.list_all_users(
        db=db,
        skip=skip,
        limit=limit,
        role=role,
        is_active=is_active,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/users/{user_id}",
    response_model=user_dtos.AdminUserDetailResponseDto,
    summary="Admin get user detail",
    description="Mengambil detail lengkap satu user untuk kebutuhan monitoring admin dan owner.",
)
def admin_get_user_detail(
    user_id: str,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = user_services.get_user_detail_admin(db=db, user_id=user_id)

    if result.error:
        raise result.error

    return result.unwrap()


@router.put(
    "/users/{user_id}",
    response_model=user_dtos.AdminUserEditResponseDto,
    summary="Owner update user profile",
    description="Memperbarui data profil user lain dari dashboard internal. Endpoint ini owner-only agar pengelolaan data user tetap terkontrol.",
)
def admin_update_user_profile(
    user_id: str,
    payload: user_dtos.AdminUserEditRequestDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.owner_access_required)],
    db: Session = Depends(get_db),
):
    result = user_services.update_user_profile_admin(
        db=db,
        user_id=user_id,
        payload=payload,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.patch(
    "/users/{user_id}/status",
    response_model=user_dtos.AdminUserStatusUpdateResponseDto,
    summary="Owner update user active status",
    description="Mengaktifkan atau menonaktifkan akun user dari dashboard internal. Endpoint ini dibatasi untuk owner agar kontrol status user internal lebih aman.",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "example": {
                        "is_active": True
                    }
                }
            }
        }
    }
)
def admin_update_user_status(
    user_id: str,
    payload: user_dtos.AdminUserStatusUpdateRequestDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.owner_access_required)],
    db: Session = Depends(get_db),
):
    result = user_services.update_user_active_status_admin(
        db=db,
        user_id=user_id,
        is_active=payload.is_active,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/dashboard/summary",
    response_model=admin_dashboard_dtos.AdminDashboardSummaryResponseDto,
    summary="Admin dashboard summary",
    description="Mengambil ringkasan metrik utama untuk landing dashboard admin.",
)
def admin_dashboard_summary(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = get_admin_dashboard_summary(db=db)

    if result.error:
        raise result.error

    return result.unwrap()


@router.get(
    "/profile",
    response_model=user_dtos.AdminSelfProfileResponseDto,
    summary="Admin get own profile",
    description="Mengambil profil akun internal yang sedang login untuk kebutuhan halaman profile dashboard.",
)
def admin_get_my_profile(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = user_services.get_admin_profile(db=db, user_id=jwt_token.id)

    if result.error:
        raise result.error

    return result.unwrap()


@router.put(
    "/edit-info",
    response_model=user_dtos.UserEditResponseDto,
    summary="Admin update own profile without photo",
    description="Memperbarui profil pribadi akun internal yang sedang login tanpa mengganti foto.",
)
async def admin_update_my_profile(
    payload: user_dtos.UserEditProfileDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = user_services.update_admin_profile(
        db=db,
        user_id=jwt_token.id,
        payload=payload,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.put(
    "/edit-photo",
    response_model=user_dtos.UserEditPhotoProfileResponseDto,
    summary="Admin update own profile photo",
    description="Memperbarui foto profil akun internal yang sedang login.",
)
async def admin_update_my_photo(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
):
    result = await user_services.update_admin_photo(
        db=db,
        user_id=jwt_token.id,
        file=file,
    )

    if result.error:
        raise result.error

    return result.unwrap()


@router.put(
    "/change-password",
    response_model=user_dtos.ChangePasswordResponseDto,
    summary="Admin change own password",
    description="Mengganti password akun internal yang sedang login dengan verifikasi password lama.",
)
async def admin_change_my_password(
    payload: user_dtos.ChangePasswordDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.admin_access_required)],
    db: Session = Depends(get_db),
):
    result = await user_services.change_admin_password(
        db=db,
        user_id=jwt_token.id,
        payload=payload,
    )

    if result.error:
        raise result.error

    return result.unwrap()

## == USER - FORGOT_PASSWORD == ##
@router.post(
    "/forgot-password",
    response_model=user_dtos.ForgotPasswordResponseDto,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Email not found."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Failed to send reset password email",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Failed to send reset password email: {error_message}"
                    }
                }
            }
        }
    },
    summary="Send internal password reset email",
    description="Mengirim email reset password untuk akun internal dashboard admin dan owner."
)
def admin_forgot_password(payload: user_dtos.ForgotPasswordDto, db: Session = Depends(get_db)):
    result = user_services.send_reset_password_request(db, payload)

    if result.error:
        raise result.error

    return result.unwrap()


## == ADMIN - CONFIRM_NEW_PASSWORD == ##
@router.post(
    "/password-reset/confirm",
    response_model=user_dtos.ResetPasswordResponseDto,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Email not found",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Email not found."
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid password criteria",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Password must meet the required criteria."
                    }
                }
            }
        },
        status.HTTP_406_NOT_ACCEPTABLE: {
            "description": "Invalid verification code",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 406,
                        "error": "Verification Code not Allowed",
                        "message": "Invalid verification code."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Failed to reset password",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Failed to reset password: {error_message}"
                    }
                }
            }
        }
    },
    summary="Confirm internal password reset",
    description="Mengonfirmasi reset password untuk akun internal dashboard admin dan owner."
)
def admin_confirm_reset_password(payload: user_dtos.ResetPasswordDto, db: Session = Depends(get_db)):
    result = user_services.confirm_password_reset(payload=payload, db=db)

    if result.error:
        raise result.error

    return result.unwrap()

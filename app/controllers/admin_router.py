from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.libs.sql_alchemy_lib import get_db
from app.libs.jwt_lib import jwt_service, jwt_dto

from app.services import user_services, order_services, payment_services
from app.dtos import user_dtos, order_dtos, payment_dtos


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
    print(f"User info from login: {user_data['user']}")  # Log untuk memastikan data user

    return {
        "status_code": status.HTTP_200_OK,
        "message": "Your user account has been logged in successfully",
        "data":user_data
    }


@router.get(
    "/orders",
    response_model=order_dtos.GetOrderInfoResponseDto,
    summary="Admin get all orders"
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
    summary="Admin get order detail"
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
    summary="Admin update order status"
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
    summary="Admin get all payments"
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
    summary="Admin get payment detail by order"
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

## == USER - FORGOT_PASSWORD == ##
# @router.post(
#     "/forgot-password",
#     # response_model=jwt_dto.AccessTokenDto,
#     response_model= user_dtos.ForgotPasswordResponseDto,
#     responses={
#         status.HTTP_404_NOT_FOUND: {
#             "description": "Email not found",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 404,
#                         "error": "Not Found",
#                         "message": "Email not found."
#                     }
#                 }
#             }
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "description": "Failed to send reset password email",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 500,
#                         "error": "Internal Server Error",
#                         "message": "Failed to send reset password email: {error_message}"
#                     }
#                 }
#             }
#         }
#     },
#     summary="Send password reset email"
# )
# def forgot_password(payload: user_dtos.ForgotPasswordDto, db: Session = Depends(get_db)):    
#     """
#     Kirim permintaan reset password ke email.

#     Kriteria Password:
#     - Password harus minimal 8 karakter.
#     - Password harus mengandung setidaknya satu huruf besar.
#     - Password harus mengandung setidaknya satu huruf kecil.
#     - Password harus mengandung setidaknya satu angka.
#     - Password harus mengandung setidaknya satu karakter spesial.
#     """
#     # Implementasi send_reset_password_request yang mengirim email dengan token
#     result = user_services.send_reset_password_request(db, payload)  # Pass the DTO directly
#     return result.unwrap()


## == USER - CONFIRM_NEW_PASSWORD == ##
# @router.post(
#     "/password-reset/confirm/",
#     response_model=user_dtos.ConfirmResetPasswordResponseDto,
#     responses={
#         status.HTTP_404_NOT_FOUND: {
#             "description": "Email not found",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 404,
#                         "error": "Not Found",
#                         "message": "Email not found."
#                     }
#                 }
#             }
#         },
#         status.HTTP_400_BAD_REQUEST: {
#             "description": "Invalid password criteria",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 400,
#                         "error": "Bad Request",
#                         "message": "Password must meet the required criteria."
#                     }
#                 }
#             }
#         },
#         status.HTTP_500_INTERNAL_SERVER_ERROR: {
#             "description": "Failed to reset password",
#             "content": {
#                 "application/json": {
#                     "example": {
#                         "status_code": 500,
#                         "error": "Internal Server Error",
#                         "message": "Failed to reset password: {error_message}"
#                     }
#                 }
#             }
#         }
#     },
#     summary="Confirm password reset"
# )
# def confirm_reset_password(payload: user_dtos.ConfirmResetPasswordDto, db: Session = Depends(get_db)):
#     """
#     API untuk mengkonfirmasi reset password setelah pengguna melakukannya di client-side.

#     Dengan menggunakan tautan reset password yang dikirim melalui email, 
    
#     Anda memastikan bahwa hanya pengguna yang memiliki akses ke email yang terdaftar yang dapat melakukan penggantian password.

#     Kriteria Password:
#     - Password harus minimal 8 karakter.
#     - Password harus mengandung setidaknya satu huruf besar.
#     - Password harus mengandung setidaknya satu huruf kecil.
#     - Password harus mengandung setidaknya satu angka.
#     - Password harus mengandung setidaknya satu karakter spesial.

#     Returns:

#         dict: Pesan sukses jika password berhasil direset.
#     """
#     result = user_services.confirm_password_reset(payload=payload, db=db)

#     return result.unwrap()  # Return the success response if no error

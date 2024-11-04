from typing import Annotated
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
    response_model=user_dtos.UserResponseDto,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User successfully created",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 201,
                        "message": "User successfully created",
                        "data": {
                            "id": "be65485e-167b-446b-9ce8-0dc11e87e06b",
                            "email": "user@example.com",
                            "firstname": "Budi",
                            "lastname": "Pekerti",
                            "gender": "male",
                            "phone": "123456789",
                            "role": "customer",
                            "created_at": "2024-09-21T14:28:23.382Z",
                            "updated_at": "2024-09-21T14:28:23.382Z"
                        }
                    }
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "User already exists (email or phone conflict)",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Email already exists. Please use a different email."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Server error while creating user",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Database Error",
                        "message": "An error occurred while creating the user. Please try again later."
                    }
                }
            }
        }
    },
    summary="Register a new user"
)
def create_user(user: user_dtos.UserCreateDto, db: Session = Depends(get_db)):
    """
    # Register User Baru #

    Endpoint ini digunakan untuk membuat akun user baru.

    **Return:**

    - **201 Created**: User berhasil dibuat.
    - **400 Bad Request**: User sudah ada (email atau nomor telepon sudah terdaftar).
        - Terjadi ketika email atau nomor telepon sudah terdaftar sebelumnya.
    - **500 Internal Server Error**: Kesalahan server saat membuat user.
        - Terjadi ketika ada kesalahan di sisi server saat membuat user.
    """
    result = user_services.create_user(db, user)
    
    return {
    "status_code": status.HTTP_201_CREATED,
    "message": "User successfully created",
    "data": result.unwrap()
}


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
    summary="User login"
)
def user_login(user: user_dtos.UserLoginPayloadDto, db: Session = Depends(get_db)):
    """
    # Login User #

    Endpoint ini digunakan untuk login user.

    **Return:**

    - **200 OK**: Login berhasil.
    - **401 Unauthorized**: Email atau password salah.
        - Terjadi ketika password yang dimasukkan tidak cocok dengan email yang diberikan.
    - **403 Forbidden**: Akun Anda tidak aktif.
        - Terjadi ketika akun user dinonaktifkan atau diblokir.
    - **404 Not Found**: User tidak ditemukan.
        - Terjadi ketika email yang diberikan tidak terdaftar.
    - **500 Internal Server Error**: Kesalahan server saat login.
        - Terjadi ketika ada kesalahan di sisi server saat login.
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

## == COBA PAKAI LOGIN USER GOOGLE == ##
@router.post(
        "/auth/google-login",
        response_model=user_dtos.GoogleLoginResponseRequestDto,
        responses={
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Unauthorized. Incorrect email or password.",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 401,
                            "error": "Unauthorized",
                            "message": "Invalid token or login failed: [FirebaseError detail here]"
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
                            "error": "Internal Server Error",
                            "message": "An unexpected error occurred: [exception message here]"
                        }
                    }
                }
            }
        },
        summary="User login use Google account"
    )
async def google_login(google_login_req: user_dtos.GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    # Login Menggunakan Akun Google #

    Endpoint ini memungkinkan user untuk login menggunakan akun Google mereka.

    **Return:**

    - **200 OK**: Login dengan Google berhasil.
    - **401 Unauthorized**: Token tidak valid atau login gagal.
        - Terjadi ketika ID token Google tidak valid atau kadaluwarsa.
    - **404 Not Found**: User tidak ditemukan.
        - Terjadi ketika email dari Google tidak terdaftar di sistem.
    - **500 Internal Server Error**: Kesalahan server saat login dengan Google.
        - Terjadi ketika ada kesalahan tidak terduga di sisi server saat login dengan Google.
    """
    user = user_services.login_with_google(db, google_login_req.id_token)
    # return user.unwrap()
    return {
    "status_code": status.HTTP_200_OK,
    "message": "Your user google account has been login successfully",
    "data": user.unwrap()  # Mengembalikan access_token yang benar
    }


## == USER - FORGOT_PASSWORD == ##
@router.post(
    "/forgot-password",
    # response_model=jwt_dto.AccessTokenDto,
    response_model= user_dtos.ForgotPasswordResponseDto,
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
    summary="Send password reset email"
)
def forgot_password(payload: user_dtos.ForgotPasswordDto, db: Session = Depends(get_db)):    
    """
    # Lupa Password #

    Endpoint ini digunakan untuk mengirim email reset password ke user.
    
    **Kriteria Password:**

    - Password harus minimal 8 karakter.
    - Password harus mengandung setidaknya satu huruf besar.
    - Password harus mengandung setidaknya satu huruf kecil.
    - Password harus mengandung setidaknya satu angka.
    - Password harus mengandung setidaknya satu karakter spesial.

    **Return:**

    - **404 Not Found**: Email tidak ditemukan.
        - Terjadi ketika email yang diberikan tidak terdaftar di sistem.
    - **500 Internal Server Error**: Gagal mengirim email reset password.
        - Terjadi ketika ada kesalahan di sisi server saat mengirim email.

    """
    # Implementasi send_reset_password_request yang mengirim email dengan token
    result = user_services.send_reset_password_request(db, payload)  # Pass the DTO directly
    return result.unwrap()


## == USER - CONFIRM_NEW_PASSWORD == ##
@router.post(
    "/password-reset/confirm",
    response_model=user_dtos.ConfirmResetPasswordResponseDto,
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
    summary="Confirm password reset"
)
def confirm_reset_password(payload: user_dtos.ConfirmResetPasswordDto, db: Session = Depends(get_db)):
    """
    # Konfirmasi Reset Password #

    Endpoint ini digunakan untuk mengkonfirmasi reset password dengan token yang dikirim melalui email.

    Dengan menggunakan tautan reset password yang dikirim melalui email, 
    
    Anda memastikan bahwa hanya pengguna yang memiliki akses ke email terdaftar yang dapat melakukan penggantian password.

    **Kriteria Password:**

    - Password harus minimal 8 karakter.
    - Password harus mengandung setidaknya satu huruf besar.
    - Password harus mengandung setidaknya satu huruf kecil.
    - Password harus mengandung setidaknya satu angka.
    - Password harus mengandung setidaknya satu karakter spesial.

    **Return:**

    - **404 Not Found**: Email tidak ditemukan.
        - Terjadi ketika email yang diberikan tidak terdaftar.
    - **400 Bad Request**: Password tidak memenuhi kriteria.
        - Terjadi ketika password baru tidak memenuhi syarat seperti panjang minimal 8 karakter, mengandung huruf besar, kecil, angka, dan simbol.
    - **500 Internal Server Error**: Gagal reset password.
        - Terjadi ketika ada kesalahan di sisi server saat melakukan reset password.
    """
    result = user_services.confirm_password_reset(payload=payload, db=db)

    return result.unwrap()  # Return the success response if no error

# == USER - GET_USER_PROFILE == ##
@router.get(
    "/profile", 
    response_model=user_dtos.UserResponseDto,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Pengguna tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Pengguna tidak ditemukan."
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Terjadi konflik saat mengakses data",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 409,
                        "error": "Conflict",
                        "message": "Terjadi konflik saat mengambil profil pengguna."
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Terjadi kesalahan di server",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan saat mengambil profil pengguna."
                    }
                }
            }
        }
    },
    summary="Get user who login profile"
)
async def get_user_profile_by_id(
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Ambil Profil Pengguna #

    Endpoint ini digunakan untuk mengambil profil pengguna berdasarkan ID yang terdapat dalam token JWT.

    **Return:**

    - **404 Not Found**: Pengguna tidak ditemukan.
        - Terjadi ketika pengguna dengan ID yang diberikan tidak terdaftar.
    - **409 Conflict**: Terjadi konflik saat mengakses data.
        - Terjadi ketika ada masalah yang berhubungan dengan data saat mencoba mengambil profil pengguna.
    - **500 Internal Server Error**: Terjadi kesalahan di server.
        - Terjadi ketika ada kesalahan di sisi server saat mengambil profil pengguna.
    """
    result = user_services.get_user_profile(db, jwt_token.id)

    if result.error:
        raise result.error
    
    return result.unwrap()


## == USER - EDIT_PROFILE_USER == ##
@router.put(
    "/edit-info",
    response_model=user_dtos.UserEditResponseDto,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "description": "Input data tidak valid",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 400,
                        "error": "Bad Request",
                        "message": "Input data tidak valid."
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Pengguna tidak ditemukan",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 404,
                        "error": "Not Found",
                        "message": "Pengguna dengan ID yang diberikan tidak ditemukan."
                    }
                }
            }
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Kesalahan server internal",
            "content": {
                "application/json": {
                    "example": {
                        "status_code": 500,
                        "error": "Internal Server Error",
                        "message": "Terjadi kesalahan yang tidak terduga: {error_message}"
                    }
                }
            }
        }
    },
    summary="Update user profile without photo"
)

async def update_user_profile_without_photo(
    user: user_dtos.UserEditProfileDto,
    jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
    db: Session = Depends(get_db)
):
    """
    # Perbarui Profil Pengguna #

    Endpoint ini digunakan untuk memperbarui profil pengguna tanpa mengubah foto profil.

    **Return:**

    - **400 Bad Request**: Input data tidak valid.
        - Terjadi ketika data yang diberikan tidak memenuhi kriteria yang ditentukan dalam DTO.
    - **404 Not Found**: Pengguna tidak ditemukan.
        - Terjadi ketika pengguna dengan ID yang diberikan tidak ditemukan dalam database.
    - **500 Internal Server Error**: Kesalahan server internal.
        - Terjadi ketika ada kesalahan di sisi server saat memproses permintaan.
    """
    result = user_services.user_edit(
        jwt_token.id,
        db=db,
        user=user
    )

    if result.error:
        raise result.error

    return result.unwrap()

@router.put(
    "/edit-photo", 
    response_model=user_dtos.UserEditPhotoProfileResponseDto,
    responses={
        200: {
            "description": "Foto profil berhasil diperbarui",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Foto profil berhasil diperbarui",
                        "data": {
                            "photo_url": "https://example.com/path/to/new/photo.png"
                        }
                    }
                }
            },
        },
        400: {
            "description": "File tidak valid atau format salah",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "File format not allowed. Please upload one of the following formats: png, jpeg, jpg, webp",
                    }
                }
            },
        },
        401: {
            "description": "Unauthorized: Token JWT tidak valid atau kadaluarsa",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Unauthorized: Token JWT tidak valid atau kadaluarsa",
                    }
                }
            },
        },
        413: {
            "description": "Ukuran file terlalu besar",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "File too large. Maximum allowed size is 300 KB"
                    }
                }
            },
        },
        500: {
            "description": "Kesalahan internal server",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "message": "Internal Server Error",
                    }
                }
            },
        },
    },
    summary="Update user profile photo"
)
async def update_only_photo(
        file: UploadFile = None,  # Jika opsional, tetap `None`; jika wajib, gunakan `File(...)`
        jwt_token: jwt_service.TokenPayLoad = Depends(jwt_service.get_jwt_pyload),
        db: Session = Depends(get_db)
):
    """
    # Ganti Photo #

    Endpoint untuk mengupdate foto profil pengguna.
    
    - **file**: File gambar yang akan diunggah (opsional).
    - **jwt_token**: Token JWT yang berisi informasi pengguna (wajib).
    - **db**: Koneksi database.

    ### Response:
    - 200: Foto profil berhasil diperbarui.
    - 400: Format file tidak diperbolehkan atau file tidak valid.
    - 401: Pengguna tidak diotorisasi (token tidak valid).
    - 413: Ukuran file melebihi batas yang diizinkan.
    - 500: Kesalahan internal server.
    """
    
    # Pastikan untuk menangani kasus di mana `file` adalah None di dalam layanan Anda
    result = await user_services.update_my_photo(db, jwt_token.id, file)
    
    if result.error:
        raise result.error
    
    return result.unwrap()

@router.put(
        "/change-password", 
        response_model=user_dtos.ChangePasswordResponseDto,
        responses={
            status.HTTP_200_OK: {
                "description": "Password changed successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 200,
                            "message": "Password has been changed successfully",
                            "data": {
                                "old_password": "********",
                                "new_password": "********"
                            }
                        }
                    }
                }
            },
            status.HTTP_400_BAD_REQUEST: {
                "description": "Invalid password criteria or old password does not match",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 400,
                            "error": "Bad Request",
                            "message": "Old password is incorrect or new password does not meet criteria."
                        }
                    }
                }
            },
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Unauthorized access",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 401,
                            "error": "Unauthorized",
                            "message": "Authentication credentials were not provided or invalid."
                        }
                    }
                }
            },
            status.HTTP_500_INTERNAL_SERVER_ERROR: {
                "description": "Failed to change password",
                "content": {
                    "application/json": {
                        "example": {
                            "status_code": 500,
                            "error": "Internal Server Error",
                            "message": "An error occurred while changing the password: [error_message]"
                        }
                    }
                }
            }
        },
        summary="Change user password"
    )
async def change_password(
        payload: user_dtos.ChangePasswordDto,
        jwt_token: Annotated[jwt_dto.TokenPayLoad, Depends(jwt_service.get_jwt_pyload)],
        db: Session = Depends(get_db)):
    
    """
    # Ganti Password #

    Endpoint ini memungkinkan user untuk mengganti password lama dengan yang baru.

    **Kriteria Password:**

    - Password harus minimal 8 karakter.
    - Password harus mengandung setidaknya satu huruf besar.
    - Password harus mengandung setidaknya satu huruf kecil.
    - Password harus mengandung setidaknya satu angka.
    - Password harus mengandung setidaknya satu karakter spesial.

    **Return:**

    - **200 OK**: Password berhasil diganti.
    - **400 Bad Request**: Password tidak memenuhi kriteria.
        - Terjadi ketika password baru tidak memenuhi syarat seperti panjang minimal 8 karakter, mengandung huruf besar, kecil, angka, dan simbol.
    - **401 Unauthorized**: Autentikasi gagal atau token tidak valid.
        - Terjadi ketika token JWT yang digunakan untuk autentikasi tidak valid atau sudah kadaluwarsa.
    - **500 Internal Server Error**: Kesalahan server saat mengganti password.
        - Terjadi ketika ada kesalahan di sisi server saat mengganti password.
    """
    result = await user_services.change_password(
        jwt_token.id,
        db=db, 
        payload=payload
    )

    if result.error:
        raise result.error

    return result.unwrap()  # Return the success response if no error

    # return {
    #     "message": "Password has been changed successfully",
    #     "data": {
    #         "old_password": user.old_password,
    #         "new_password": user.new_password
    #     }
    # }

























# @router.post("/reset-password", response_model=user_dtos.ResetPasswordResponseDto)
# def reset_password(payload: user_dtos.ResetPasswordDto, db: Session = Depends(get_db)):
#     try:
#         # Panggil service untuk memverifikasi token dan reset password
#         user_services.reset_password(payload, db)
        
#         # Jika berhasil, kembalikan response yang sesuai
#         return user_dtos.ResetPasswordResponseDto(
#             status_code=200,
#             message="Password has been reset successfully.",
#             data=payload
#         )
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message=f"Error processing password reset: {str(e)}"
#         )

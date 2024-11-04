from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.utils.firebase_utils import create_firebase_user, send_verification_email

from app.models.user_model import UserModel
from app.dtos import user_dtos
from app.libs import password_lib
from app.utils import optional, error_parser

from app.dtos.error_response_dtos import ErrorResponseDto

def create_user(
        db: Session, 
        user: user_dtos.UserCreateDto
    ) -> optional.Optional[UserModel, Exception]:
    try:
        # Validasi input email dan password
        if not user.email or not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Email and password must be provided."
                ).dict()
            )

        # Buat user di Firebase
        firebase_user = create_firebase_user(user.email, user.password)

        if firebase_user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Failed to create user in Firebase."
                ).dict()
            )

        # Membuat instance user baru
        user_model = UserModel(
            firstname=user.firstname,
            lastname=user.lastname,
            gender=user.gender,
            email=firebase_user.email,
            phone=user.phone,
            hash_password=password_lib.get_password_hash(password=user.password),
            firebase_uid=firebase_user.uid,
            role="customer"
        )

        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        send_verification_email(firebase_user, user.firstname)

        return optional.build(data=user_model)

    except IntegrityError as ie:
        db.rollback()
        if 'email' in str(ie.orig):
            message = "The email address is already in use by another account."
        elif 'phone' in str(ie.orig):
            message = "The phone number is already in use by another account."
        else:
            message = "Duplicate data found."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message=message
            ).dict()
        )

    except SQLAlchemyError:
        return optional.build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))
    # except SQLAlchemyError:
    #     db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=ErrorResponseDto(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             error="Internal Server Error",
    #             message="An error occurred while creating the user. Please try again later."
    #         ).dict()
    #     )
    
    # except HTTPException as http_ex:
    #     # Kembalikan langsung HTTPException tanpa perubahan
    #     raise http_ex

    # except Exception as e:
    #     db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=ErrorResponseDto(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             error="Internal Server Error",
    #             message=f"Unexpected error: {str(e)}"
    #         ).dict()
    #     )


def create_admin(
        db: Session, 
        user: user_dtos.UserCreateDto
    ) -> optional.Optional[UserModel, Exception]:
    try:
        # Validasi input email dan password
        if not user.email or not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Email and password must be provided."
                ).dict()
            )

        # Buat user di Firebase
        firebase_user = create_firebase_user(user.email, user.password)

        if firebase_user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error="Bad Request",
                    message="Failed to create user in Firebase."
                ).dict()
            )

        # Membuat instance user baru
        user_model = UserModel()
        user_model.firstname = user.firstname
        user_model.lastname = user.lastname
        user_model.gender = user.gender
        user_model.email = firebase_user.email
        user_model.phone = user.phone
        user_model.hash_password = password_lib.get_password_hash(password=user.password)

        # Mengisi role secara otomatis sebagai 'customer'
        user_model.role = "admin"
        print(f"Role being set: {user_model.role}")  # Debug role sebelum commit

        # Menambahkan user ke dalam database
        db.add(user_model)
        db.commit()
        db.refresh(user_model)  # Memastikan data yang baru ditambahkan ter-refresh
        
        print(f"Role after refresh: {user_model.role}")  # Debug role setelah commit
        
        # Kirim email verifikasi setelah user berhasil dibuat
        send_verification_email(firebase_user, user.firstname)

        return optional.build(data=user_model)

    except IntegrityError as ie:
        db.rollback()
        if 'email' in str(ie.orig):
            message = "The email address is already in use by another account."
        elif 'phone' in str(ie.orig):
            message = "The phone number is already in use by another account."
        else:
            message = "Duplicate data found."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponseDto(
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Bad Request",
                message=message
            ).dict()
        )

    except SQLAlchemyError:
        return optional.build(error= HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponseDto(
                status_code=status.HTTP_409_CONFLICT,
                error="Conflict",
                message=f"Database conflict: {str(e)}"
            ).dict()
        ))
    
    except HTTPException as e:
        # Menangani error yang dilempar oleh Firebase atau proses lainnya
        return optional.build(error=e)

    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"Unexpected error: {str(e)}"
            ).dict()
        ))
    


# def create_user(db: Session, user: user_dtos.UserCreateDto) -> optional.Optional[UserModel, Exception]:
#     try:
#         # Validasi input email dan password
#         if not user.email or not user.password:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 error="Bad Request",
#                 message="Email and password must be provided."
#             )

#         # Buat user di Firebase
#         firebase_user = create_firebase_user(user.email, user.password)

#         if firebase_user is None:  # Pastikan firebase_user tidak None
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 error="Bad Request",
#                 message="Failed to create user in Firebase."
#             )

#         # Membuat instance user baru
#         user_model = UserModel(
#             firstname=user.firstname,  # Ambil firstname dari DTO
#             lastname=user.lastname,
#             gender=user.gender,
#             email=firebase_user.email,
#             phone=user.phone,
#             hash_password=password_lib.get_password_hash(password=user.password),
#             firebase_uid=firebase_user.uid,
#             role="customer"  # Role otomatis sebagai 'customer'
#         )

#         # Menambahkan user ke dalam database
#         db.add(user_model)
#         db.commit()
#         db.refresh(user_model)  # Memastikan data yang baru ditambahkan ter-refresh
        
#         # Kirim email verifikasi setelah user berhasil dibuat
#         send_verification_email(firebase_user, user.firstname)

#         return optional.build(data=user_model)

#     except IntegrityError as ie:
#         db.rollback()  # Rollback jika ada kesalahan integritas data (misal, duplikasi email atau username)

#         # Menentukan apakah kesalahan berasal dari email atau username yang sudah ada
#         if 'email' in str(ie.orig):
#             message = "Email already exists. Please use a different email."
#         elif 'phone' in str(ie.orig):
#             message = "Phone already exists. Please choose a different phone."
#         else:
#             message = "Duplicate data found."

#         # Mengembalikan kesalahan dengan pesan yang jelas
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             error= "Bad Request",
#             message=message
#         ))

#     except SQLAlchemyError as e:
#         db.rollback()  # Rollback untuk semua error SQLAlchemy umum lainnya
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message="An error occurred while creating the user. Please try again later."
#         ))
    
#     except HTTPException as http_ex:
#         db.rollback()  # Rollback jika terjadi error dari Firebase
#         # Langsung kembalikan error dari Firebase tanpa membuat response baru
#         return optional.build(error=http_ex)

#     except Exception as e:
#         db.rollback()  # Rollback untuk error tak terduga
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message=f"Unexpected error: {str(e)}"
#         ))


# def create_admin(db: Session, user: user_dtos.UserCreateDto) -> optional.Optional[UserModel, Exception]:
#     try:
#         # Validasi input email dan password
#         if not user.email or not user.password:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 error="Bad Request",
#                 message="Email and password must be provided."
#             )

#         # Buat user di Firebase
#         firebase_user = create_firebase_user(user.email, user.password)

#         if firebase_user is None:  # Pastikan firebase_user tidak None
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 error="Bad Request",
#                 message="Failed to create user in Firebase."
#             )

#         # Membuat instance user baru
#         user_model = UserModel()
#         user_model.firstname = user.firstname
#         user_model.lastname = user.lastname
#         user_model.gender = user.gender
#         user_model.email = firebase_user.email
#         user_model.phone = user.phone
#         user_model.hash_password = password_lib.get_password_hash(password=user.password)

#         # Mengisi role secara otomatis sebagai 'customer'
#         user_model.role = "admin"
#         print(f"Role being set: {user_model.role}")  # Debug role sebelum commit

#         # Menambahkan user ke dalam database
#         db.add(user_model)
#         db.commit()
#         db.refresh(user_model)  # Memastikan data yang baru ditambahkan ter-refresh
        
#         print(f"Role after refresh: {user_model.role}")  # Debug role setelah commit
        
#         # Kirim email verifikasi setelah user berhasil dibuat
#         send_verification_email(firebase_user, user.firstname)

#         return optional.build(data=user_model)

#     except IntegrityError as ie:
#         db.rollback()  # Rollback jika ada kesalahan integritas data (misal, duplikasi email atau username)

#         # Menentukan apakah kesalahan berasal dari email atau username yang sudah ada
#         if 'email' in str(ie.orig):
#             message = "Email already exists. Please use a different email."
#         elif 'phone' in str(ie.orig):
#             message = "Phone already exists. Please choose a different phone."
#         else:
#             message = "Duplicate data found."

#         # Mengembalikan kesalahan dengan pesan yang jelas
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             error= "Bad Request",
#             message=message
#         ))

#     except SQLAlchemyError as e:
#         db.rollback()  # Rollback untuk semua error SQLAlchemy umum lainnya
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message="An error occurred while creating the user. Please try again later."
#         ))
    
#     except HTTPException as http_ex:
#         db.rollback()  # Rollback jika terjadi error dari Firebase
#         # Langsung kembalikan error dari Firebase tanpa membuat response baru
#         return optional.build(error=http_ex)

#     except Exception as e:
#         db.rollback()  # Rollback untuk error tak terduga
#         return optional.build(error=HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             error="Internal Server Error",
#             message=f"Unexpected error: {str(e)}"
#         ))



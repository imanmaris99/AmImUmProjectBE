# services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

from app.models.user_model import UserModel
from app.utils import optional

def login_with_google(db: Session, id_token: str):
    try:
        # Verifikasi ID token dengan Firebase
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')

        # Cek apakah pengguna sudah ada di database
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            # Jika pengguna tidak ada, Anda bisa membuat pengguna baru
            user = UserModel(
                email=email,
                firstname=decoded_token.get('given_name', ''),
                lastname=decoded_token.get('family_name', ''),
                gender=decoded_token.get('gender', None),
                phone=decoded_token.get('phone', None)
                # Tambahkan data lainnya sesuai kebutuhan
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return optional.build (data=user)
    
    except FirebaseError as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="Unauthorized",
            message="Invalid token or login failed :" + str(e)
        ))
    
    except Exception as e:
        return optional.build(error=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="Internal Server Error",
            message="An unexpected error occurred :" + str(e)
        ))
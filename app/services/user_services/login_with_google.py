# services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from app.models.user_model import UserModel

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
                # Tambahkan data lainnya sesuai kebutuhan
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="Unauthorized",
            message="Invalid token or login failed"
        )

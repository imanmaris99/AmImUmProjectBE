import io
import os
import time
import uuid
import hashlib
import logging

import requests
from PIL import Image
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos import production_dtos
from app.dtos.error_response_dtos import ErrorResponseDto
from app.libs.redis_config import redis_client
from app.libs.upload_image_to_supabase import validate_file
from app.models.production_model import ProductionModel
from app.services.production_services.support_function import handle_db_error
from app.utils.result import build, Result

logger = logging.getLogger(__name__)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
TARGET_MAX_OUTPUT_SIZE = 1 * 1024 * 1024
TARGET_IDEAL_OUTPUT_SIZE = 500 * 1024


def _cloudinary_creds() -> tuple[str, str, str]:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    api_key = os.getenv("CLOUDINARY_API_KEY", "").strip()
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip()
    if not cloud_name or not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="Cloudinary env belum lengkap")
    return cloud_name, api_key, api_secret


def _extract_public_id_from_cloudinary_url(url: str) -> str | None:
    if "/image/upload/" not in url:
        return None
    try:
        tail = url.split("/image/upload/", 1)[1]
        parts = tail.split("/")
        if parts and parts[0].startswith("v") and parts[0][1:].isdigit():
            parts = parts[1:]
        if not parts:
            return None
        path = "/".join(parts)
        if "." in path:
            path = path.rsplit(".", 1)[0]
        return path
    except Exception:
        return None


def _delete_from_cloudinary(url: str) -> None:
    public_id = _extract_public_id_from_cloudinary_url(url)
    if not public_id:
        return

    cloud_name, api_key, api_secret = _cloudinary_creds()
    timestamp = int(time.time())
    params_to_sign = f"public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()

    destroy_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/destroy"
    data = {
        "public_id": public_id,
        "timestamp": timestamp,
        "api_key": api_key,
        "signature": signature,
    }
    try:
        requests.post(destroy_url, data=data, timeout=20)
    except Exception:
        pass


def _upload_to_cloudinary(image_bytes: bytes, production_id: int, public_id_seed: str) -> str:
    cloud_name, api_key, api_secret = _cloudinary_creds()

    timestamp = int(time.time())
    folder = f"amimum/productions/{production_id}/logo"
    public_id = public_id_seed
    transformation = "f_auto,q_auto"
    params_to_sign = f"folder={folder}&public_id={public_id}&timestamp={timestamp}&transformation={transformation}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    files = {"file": (f"{public_id}.webp", image_bytes, "image/webp")}
    data = {
        "api_key": api_key,
        "timestamp": timestamp,
        "folder": folder,
        "public_id": public_id,
        "signature": signature,
        "transformation": transformation,
        "overwrite": "true",
    }

    response = requests.post(upload_url, files=files, data=data, timeout=30)
    if response.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload gagal: {response.text}")

    payload = response.json()
    return payload.get("secure_url")


async def post_logo(
        db: Session,
        production_id: int, 
        user_id: str, 
        file: UploadFile
    ) -> Result[ProductionModel, Exception]:
    try:

        # Buat instance dari ProductionModel
        # logo_model = ProductionModel(fk_admin_id=user_id)
        # Ambil instance dari ProductionModel berdasarkan ID
        logo_model = db.query(ProductionModel).filter(ProductionModel.id == production_id).first()

        if not logo_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Production with ID {production_id} not found"
                ).dict()
            )

        # Langkah 2: Validasi file jika ada
        if file:
            validate_file(file)  # existing validation extension

            if file.content_type not in ALLOWED_MIME:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")

            raw = await file.read()
            if len(raw) > MAX_FILE_SIZE:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large")

            logger.debug("Uploading production logo to Cloudinary production_id=%s filename=%s", production_id, file.filename)

            final_bytes = raw
            try:
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                img.thumbnail((1200, 1200))

                quality_steps = [82, 78, 74, 70, 66, 62, 58, 54, 50]
                current = img
                compressed = None

                while True:
                    for quality in quality_steps:
                        buffer = io.BytesIO()
                        current.save(buffer, format="WEBP", quality=quality, optimize=True)
                        size = buffer.tell()
                        if size <= TARGET_IDEAL_OUTPUT_SIZE:
                            compressed = buffer.getvalue()
                            break
                        if size <= TARGET_MAX_OUTPUT_SIZE:
                            compressed = buffer.getvalue()
                    if compressed is not None:
                        break

                    w, h = current.size
                    if max(w, h) <= 700:
                        buffer = io.BytesIO()
                        current.save(buffer, format="WEBP", quality=50, optimize=True)
                        compressed = buffer.getvalue()
                        break

                    current = current.resize((int(w * 0.85), int(h * 0.85)))

                final_bytes = compressed or raw
            except Exception:
                final_bytes = raw

            if len(final_bytes) > TARGET_MAX_OUTPUT_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Gagal mengompres logo ke <= 1MB. Gunakan logo resolusi lebih kecil."
                )

            old_logo_url = logo_model.photo_url
            public_url = _upload_to_cloudinary(final_bytes, production_id, f"logo-{uuid.uuid4().hex[:12]}")

            if not public_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        error="Internal Server Error",
                        message="Failed to upload image."
                    ).dict()
                )

            logo_model.photo_url = public_url
            if old_logo_url and old_logo_url != public_url:
                _delete_from_cloudinary(old_logo_url)

        db.add(logo_model)
        db.commit()
        db.refresh(logo_model)

        # Buat instance dari UserEditProfileDto
        user_response = production_dtos.PostLogoCompanyDto(
            photo_url=logo_model.photo_url,
        )

        # Invalidate the cached wishlist for this user
        patterns_to_invalidate = [
            f"productions:*",
            f"all_brand_by_categories:*",
            f"brand_promotions:*",
            f"production:{production_id}"
        ]
        for pattern in patterns_to_invalidate:
            for key in redis_client.scan_iter(pattern):
                redis_client.delete(key)

        # return build(data=user_model)
        return build(data=production_dtos.PostLogoCompanyResponseDto(
            status_code=200,
            message="Your profile has been successfully updated",
            data=user_response
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)
    
    except HTTPException as http_ex:
        db.rollback()  # Rollback jika terjadi error dari Firebase
        return build(error=http_ex)
    
    except Exception as e:
        logger.exception("Unexpected error while updating production logo production_id=%s", production_id)
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))




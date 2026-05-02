import io
import logging
import os
import uuid
import time
import hashlib
import requests
from PIL import Image

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dtos.error_response_dtos import ErrorResponseDto
from app.dtos.pack_type_dtos import EditPhotoProductDto, EditPhotoProductResponseDto
from app.libs.upload_image_to_supabase import validate_file
from app.libs.supabase_client import supabase
from app.models.pack_type_model import PackTypeModel
from app.services.pack_type_services.support_function import handle_db_error
from app.utils.result import build, Result

logger = logging.getLogger(__name__)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
TARGET_MAX_OUTPUT_SIZE = 100 * 1024
TARGET_IDEAL_OUTPUT_SIZE = 50 * 1024


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


def _upload_to_cloudinary(image_bytes: bytes, type_id: int, public_id_seed: str) -> str:
    cloud_name, api_key, api_secret = _cloudinary_creds()

    timestamp = int(time.time())
    folder = f"amimum/variants/{type_id}"
    public_id = f"{public_id_seed}"

    params_to_sign = f"folder={folder}&public_id={public_id}&timestamp={timestamp}{api_secret}"
    signature = hashlib.sha1(params_to_sign.encode("utf-8")).hexdigest()

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    files = {"file": (f"{public_id}.webp", image_bytes, "image/webp")}
    data = {
        "api_key": api_key,
        "timestamp": timestamp,
        "folder": folder,
        "public_id": public_id,
        "signature": signature,
    }

    response = requests.post(upload_url, files=files, data=data, timeout=30)
    if response.status_code >= 300:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload gagal: {response.text}")

    payload = response.json()
    return payload.get("secure_url")


def _upload_to_supabase_bytes(image_bytes: bytes, type_id: int, user_id: str) -> str | None:
    filename = f"images/product_picture/{user_id}_{int(time.time())}_variant_{type_id}.webp"
    upload_response = supabase.storage.from_("AmimumProject-storage").upload(
        filename,
        image_bytes,
        {"content-type": "image/webp"}
    )
    if isinstance(upload_response, dict) and upload_response.get("error"):
        return None
    public_url = supabase.storage.from_("AmimumProject-storage").get_public_url(filename)
    return public_url if isinstance(public_url, str) else None


async def post_photo(
        db: Session,
        type_id: int,
        user_id: str,
        file: UploadFile
    ) -> Result[PackTypeModel, Exception]:
    try:
        image_model = db.query(PackTypeModel).filter(PackTypeModel.id == type_id).first()

        if not image_model:
            return build(error= HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponseDto(
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Not Found",
                    message=f"Info about variant product with ID {type_id} not found"
                ).dict()
            ))

        if file:
            validate_file(file)
            if file.content_type not in ALLOWED_MIME:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")

            raw = await file.read()
            if len(raw) > MAX_FILE_SIZE:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image too large")

            final_bytes = raw
            try:
                img = Image.open(io.BytesIO(raw)).convert("RGB")
                img.thumbnail((1600, 1600))

                quality_steps = [82, 78, 74, 70, 66, 62, 58, 54, 50]
                current_image = img
                compressed = None

                while True:
                    for quality in quality_steps:
                        buffer = io.BytesIO()
                        current_image.save(buffer, format="WEBP", quality=quality, optimize=True)
                        size = buffer.tell()
                        if size <= TARGET_IDEAL_OUTPUT_SIZE:
                            compressed = buffer.getvalue()
                            break
                        if size <= TARGET_MAX_OUTPUT_SIZE:
                            compressed = buffer.getvalue()
                    if compressed is not None:
                        break

                    w, h = current_image.size
                    if max(w, h) <= 900:
                        buffer = io.BytesIO()
                        current_image.save(buffer, format="WEBP", quality=50, optimize=True)
                        compressed = buffer.getvalue()
                        break

                    current_image = current_image.resize((int(w * 0.85), int(h * 0.85)))

                final_bytes = compressed or raw

            except Exception:
                final_bytes = raw

            if len(final_bytes) > TARGET_MAX_OUTPUT_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Gagal mengompres gambar ke <= 100KB. Gunakan foto resolusi lebih kecil."
                )

            old_url = image_model.img
            public_url = None
            uploaded_provider = "cloudinary"
            try:
                public_url = _upload_to_cloudinary(final_bytes, type_id, f"variant-{uuid.uuid4().hex[:12]}")
            except Exception:
                logger.warning("Cloudinary upload failed for variant %s, fallback to Supabase", type_id)
                public_url = _upload_to_supabase_bytes(final_bytes, type_id, user_id)
                uploaded_provider = "supabase"

            if not public_url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=ErrorResponseDto(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        error="Internal Server Error",
                        message="Failed to upload image on all storage providers."
                    ).dict()
                )

            image_model.img = public_url
            if old_url and uploaded_provider == "cloudinary":
                _delete_from_cloudinary(old_url)

        db.add(image_model)
        db.commit()
        db.refresh(image_model)

        updated_response = EditPhotoProductDto(
            img=image_model.img,
        )

        return build(data=EditPhotoProductResponseDto(
            status_code=200,
            message="Edit photo product has been success",
            data=updated_response
        ))

    except SQLAlchemyError as e:
        return handle_db_error(db, e)

    except HTTPException as http_ex:
        db.rollback()
        return build(error=http_ex)

    except Exception as e:
        logger.exception("Unexpected error while updating pack type photo type_id=%s", type_id)
        return build(error= HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseDto(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error="Internal Server Error",
                message=f"An error occurred: {str(e)}"
            ).dict()
        ))

import re
import time
import io
from fastapi import UploadFile, HTTPException, status
from PIL import Image
from app.libs.supabase_client import supabase

# Konstanta untuk validasi file
ALLOWED_EXTENSIONS = ['png', 'jpeg', 'jpg', 'webp']
MAX_FILE_SIZE = 300 * 1024  # Maksimum ukuran file 300KB 

def validate_file(file: UploadFile):
    """
    Validasi file untuk memastikan format dan ukuran yang diizinkan.
    """
    # Langkah 1: Periksa format file
    filename = file.filename
    file_extension = filename.split('.')[-1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            error="Bad Request",
            message=f"File format not allowed. Please upload one of the following formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Langkah 2: Periksa ukuran file
    file.file.seek(0, 2)  # Pindahkan pointer ke akhir file untuk mendapatkan ukuran
    file_size = file.file.tell()  # Dapatkan ukuran file
    file.file.seek(0)  # Kembalikan pointer ke awal agar file bisa dibaca kembali setelah validasi

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error="Request Entity Too Large",
            message=f"File too large. Maximum allowed size is {MAX_FILE_SIZE / 1024} KB"
        )

async def compress_image(file: UploadFile) -> bytes:
    """
    Mengompresi gambar menggunakan Pillow.
    """
    image = Image.open(file.file)
    img_byte_arr = io.BytesIO()
    
    # Mengompresi gambar dengan kualitas 85
    image.save(img_byte_arr, format=image.format, quality=85)
    img_byte_arr.seek(0)
    
    return img_byte_arr.read()

async def upload_image_to_supabase(
        file: UploadFile, 
        bucket_name: str, 
        user_id: str, 
        folder_name: str = "", 
        old_file_url: str = None
    ) -> str:
    
    """
    Mengupload gambar yang telah dikompresi ke Supabase.
    """
    try:
        # Kompres gambar sebelum upload
        file_content = await compress_image(file)

        # Buat ID yang lebih sederhana menggunakan timestamp
        timestamp = int(time.time())
        simple_id = f"{user_id}_{timestamp}"

        # Sanitasi nama file untuk menghindari karakter yang tidak valid
        sanitized_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)

        # Buat nama file yang unik
        unique_filename = f"{simple_id}_{sanitized_filename}"
       
        # Jika ada folder_name, simpan file di dalam folder tersebut
        if folder_name:
            unique_filename = f"{folder_name}/{unique_filename}"

        # Tampilkan URL file lama yang akan dihapus
        print(f"Old file URL: {old_file_url}")

        # Hapus file lama jika ada
        if old_file_url:
            old_file_name = old_file_url.split('/')[-1].split('?')[0].strip()
            print(f"Old file name extracted: {old_file_name}")
            print(f"Attempting to delete old file: {old_file_name}")

            delete_response = supabase.storage.from_(bucket_name).remove([old_file_name])
            print(f"Delete response: {delete_response}")

            if isinstance(delete_response, dict) and 'error' in delete_response:
                raise Exception(f"Error deleting old file: {delete_response['error'].get('message', 'Unknown error')}")
            elif not delete_response:
                print("Old file not found or already deleted.")

        # Menyimpan file ke storage Supabase
        upload_response = supabase.storage.from_(bucket_name).upload(unique_filename, file_content)
        print(f"Upload response: {upload_response}")
        
        if isinstance(upload_response, dict) and 'error' in upload_response:
            raise Exception(f"Error uploading file: {upload_response['error'].get('message', 'Unknown error')}")
        elif upload_response is None:
            raise Exception("Failed to upload file.")

        # URL publik file yang diupload
        public_url_response = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        print(f"Public URL response: {public_url_response}")

        if isinstance(public_url_response, str):
            public_url = public_url_response
        else:
            raise Exception("Unexpected response format when getting public URL")

        return public_url

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

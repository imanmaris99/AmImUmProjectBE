# AmImUmHerbal - Finding Product

AmImUmHerbal adalah sebuah aplikasi yang dirancang untuk membantu pengguna menemukan produk herbal dengan mudah dan efisien. Proyek ini dibangun menggunakan FastAPI dan berbagai pustaka lainnya untuk memberikan pengalaman pengguna yang optimal.

## Fitur Utama

- **Pencarian Produk**: Pengguna dapat mencari produk herbal berdasarkan nama, kategori, atau kata kunci.
- **Detail Produk**: Menampilkan informasi mendetail tentang setiap produk termasuk deskripsi, harga, dan manfaat.
- **Tampilan Responsif**: Antarmuka yang mudah digunakan di berbagai perangkat.
- **API yang Kuat**: Backend yang dibangun menggunakan FastAPI untuk kecepatan dan performa yang tinggi.

## Teknologi yang Digunakan

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Pengelolaan Lingkungan**: Poetry
- **Keamanan**: JWT untuk otentikasi
- **Pengujian**: Pytest
- **Deployment**: Docker, Docker Compose
- **Firebase**: Untuk otentikasi pengguna
- **Supabase**: Untuk pengelolaan data dan penyimpanan cloud
- **Railway**: Untuk deployment ke produksi

## Prerequisites

Sebelum memulai, pastikan kamu sudah menginstal:

- Python 3.12 atau lebih tinggi
- PostgreSQL
- Docker & Docker Compose (untuk environment development menggunakan container)
- Poetry (untuk manajemen dependensi dan environment)

## Instalasi

Ikuti langkah-langkah berikut untuk menginstal dan menjalankan proyek:

### 1. Clone Repositori

```bash
git clone https://github.com/username/amimumherbal.git
cd amimumherbal
```

### 2. Instal Dependensi

Jika kamu menggunakan Poetry:
```bash
poetry install
```

### 3. Konfigurasi Lingkungan

Buat file .env di root folder proyek dan masukkan konfigurasi berikut:
```makefile
DATABASE_URL=postgresql://user:password@localhost:5432/mydatabase
SECRET_KEY=mysecretkey
DEBUG=True
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_PROJECT_ID=your_firebase_project_id
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SMTP_SERVER=smtp_type
SMTP_PORT=587/465
SMTP_USER=your_email
SMTP_PASSWORD=your_password
FROM_EMAIL=your_email
```

### 4. Menjalankan Database

Jika menggunakan Docker, kamu bisa menjalankan PostgreSQL melalui Docker Compose:
```bash
docker-compose up -d
```

### 5. Jalankan Migrasi Database

Jika menggunakan Alembic untuk migrasi database:
```bash
poetry run uvicorn app.main:app --reload
```
Aplikasi akan berjalan di http://127.0.0.1:8000.


## Pengujian
Untuk menjalankan pengujian unit dan integrasi, gunakan perintah berikut:

```bash
poetry run pytest
```
Pengujian juga mencakup cakupan kode dengan pytest-cov:

```bash
poetry run pytest --cov=app
```


## Pengembangan (Development)

### 1. Menjalankan Environment dengan Docker
Selama pengembangan, kamu bisa menggunakan Docker dan Docker Compose untuk menjalankan seluruh stack aplikasi, termasuk database PostgreSQL dan aplikasi FastAPI.

```bash
docker-compose -f docker-compose.dev.yml up --build
```
File docker-compose.dev.yml telah diatur untuk menjalankan container dengan pengaturan development seperti:

- Hot-reloading: Uvicorn akan secara otomatis memuat ulang jika ada perubahan kode.
- Debugging: Debug mode diaktifkan di dalam aplikasi.

### 2. Menggunakan Poetry dalam Development
#### Membuat Virtual Environment Otomatis
Poetry dapat diatur untuk membuat virtual environment di dalam folder proyek (.venv):

```bash
poetry config virtualenvs.in-project true
```
Setelah diatur, jalankan perintah ini untuk menginstall semua dependensi termasuk dependensi pengembangan:

```bash
poetry install --with dev
```
#### Menggunakan Poetry untuk Menjalankan Aplikasi
Selama development, kamu dapat menggunakan poetry run untuk menjalankan aplikasi atau perintah pengujian:

```bash
poetry run uvicorn app.main:app --reload
```
#### Migrasi Database
Untuk memastikan skema database terbaru diterapkan:

```bash
poetry run alembic upgrade head
```

### 3. Dependensi Development
Proyek ini menggunakan beberapa dependensi khusus untuk development:

- ytest: Untuk menjalankan pengujian.
- pytest-cov: Untuk melacak cakupan kode selama pengujian.
- black: Untuk auto-formatting kode.
- isort: Untuk mengatur import.
- flake8: Untuk linting kode.

Kamu dapat menjalankan semua pengujian dengan:

```bash
poetry run pytest
```

Untuk memeriksa linting dan formatting:

```bash
poetry run black --check .
poetry run flake8 .
```

### 4. Tips Pengembangan
- Hot Reloading: Uvicorn secara otomatis memuat ulang aplikasi saat ada perubahan jika dijalankan dengan flag `--reload`.
- Debugging: Gunakan tools seperti VSCode atau PyCharm untuk debugging dengan breakpoint.

## Kontribusi
Jika kamu ingin berkontribusi pada proyek ini:

1. Fork repositori ini.
Buat branch fitur baru (`git checkout -b feature/your-feature`).
2. Lakukan perubahan dan commit (`git commit -m 'Add some feature'`).
3. Push branch kamu (`git push origin feature/your-feature`).
4. Buat Pull Request.

## Lisensi
Proyek ini dilisensikan di bawah MIT License. Lihat [LICENSE]() untuk detail lebih lanjut.

## Kontak
Untuk pertanyaan atau saran, silakan hubungi:

Nama: [amimumHerbal]()
Email: [herbalamimum99@gmail.com]()

```markdown
### Penjelasan Tambahan:

- **Docker Compose**: `docker-compose.dev.yml` diatur untuk development environment (misalnya hot-reloading, debug mode).
- **Poetry**: Bagian ini menjelaskan cara mengatur virtual environment dan menggunakan Poetry untuk keperluan development.
- **Testing**: Ada instruksi tambahan tentang bagaimana menjalankan tes dan mengukur cakupan kode menggunakan `pytest` dan `pytest-cov`.
- **Linting & Formatting**: Dengan menggunakan `black`, `flake8`, dan `isort`, proses development bisa lebih terstruktur dan mudah dijaga.
```
</br>

##

<div align="center">
     <a href="https://github.com/imanmaris99" target="_blank" rel="noopener noreferrer">
        <img src="./images/logo_toko_amimum-removebg-preview.png" width="70px" />
    </a>
    <p style="font-size: 12px;">
       &copy; 2024 AmImUmHerbal. 
    </p>
</div>
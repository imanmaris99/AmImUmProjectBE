# AmImUmHerbal - Finding Product

AmImUmHerbal adalah sebuah aplikasi yang dirancang untuk membantu pengguna menemukan produk herbal dengan mudah dan efisien. Proyek ini dibangun menggunakan FastAPI dan berbagai pustaka lainnya untuk memberikan pengalaman pengguna yang optimal.

## Prototype

Prototype aplikasi AmImUmHerbal disusun menggunakan bantuan figma, berikut untuk gambaran sederhana dari aplikasi ini.
["prototype aplikasi AmImUm Herbal"](https://www.figma.com/proto/x3RYOGzVfX6MxQo8rJemJ5/Consumer-UI---AmImUm-Herbal-Shop-Mobile-App?node-id=4074-7857&node-type=canvas&t=8ExRY6YHLRclxNfF-1&scaling=scale-down&content-scaling=fixed&page-id=4074%3A7695&starting-point-node-id=4074%3A7857&show-proto-sidebar=1)

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

Buat file `.env` di root folder proyek dengan menjadikan `.env.example` sebagai template utama.

Contoh variabel yang digunakan aplikasi saat ini:
```makefile
PORT=8000
APP_DEVELOPMENT=True
HOST_URL=http://127.0.0.1:8000
SECRET_KEY=change-me

DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=amimum_db
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/amimum_db

FIREBASE_SERVICE_ACCOUNT_KEY=
SUPABASE_URL=
SUPABASE_KEY=

SMTP_SERVER=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
FROM_EMAIL=

RAJAONGKIR_API_KEY=
RAJAONGKIR_API_HOST=api.rajaongkir.com

MIDTRANS_SERVER_KEY=
MIDTRANS_CLIENT_KEY=
MIDTRANS_IS_PRODUCTION=false

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### 4. Menjalankan Database

Jika menggunakan Docker, kamu bisa menjalankan PostgreSQL melalui Docker Compose:
```bash
docker-compose up -d
```

### 5. Jalankan Migrasi Database dan Aplikasi

Untuk memastikan skema database terbaru diterapkan:
```bash
poetry run alembic upgrade head
```

Untuk menjalankan aplikasi secara lokal:
```bash
poetry run python run.py
```

Atau mode development dengan reload:
```bash
poetry run uvicorn app.main:app --reload
```

Aplikasi akan berjalan di `http://127.0.0.1:8000`.


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
Selama pengembangan atau staging, kamu bisa menggunakan Docker Compose untuk menjalankan stack aplikasi.

```bash
docker-compose up --build
```

Pastikan file `.env` sudah terisi sebelum menjalankan container, karena service `app` membaca konfigurasi dari environment tersebut.

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

## Launch Readiness Backend Checklist

Status saat ini untuk kesiapan backend menuju staging/produksi:

### Yang sudah tervalidasi
- Aplikasi dapat dijalankan secara lokal
- Endpoint dokumentasi `/docs` merespons `200`
- Endpoint OpenAPI `/openapi.json` merespons `200`
- Endpoint publik katalog berikut merespons `200`
  - `/product/all`
  - `/brand/all`
  - `/type/all`
- Flow inti telah melalui beberapa batch hardening pada area:
  - service product / pack type / production
  - checkout dan payment notification
  - auth dan email verification
  - firebase init, scheduler, storage, Redis, Midtrans, Supabase config

### Yang masih perlu divalidasi sebelum launch penuh
- Uji endpoint yang membutuhkan autentikasi dengan skenario nyata
- Uji register → verify email → login → checkout → payment secara end-to-end
- Validasi integrasi eksternal dengan kredensial produksi/staging yang final:
  - Firebase
  - Supabase
  - SMTP
  - Midtrans
  - RajaOngkir
  - Redis
- Validasi migrasi database pada environment staging/production
- Review CORS dan host/domain final
- Review pengelolaan file upload/images pada environment deploy final

### Catatan blocker saat ini
- Folder `tests/` belum berisi suite test yang memadai, jadi regresi masih banyak bergantung pada smoke test manual
- README dan checklist deploy masih perlu terus dijaga sinkron mengikuti perubahan implementasi
- Belum ada healthcheck/deploy verification formal di level container/orchestrator

### Rekomendasi langkah berikut
1. Siapkan environment staging final berdasarkan `.env.example`
2. Jalankan migrasi database di staging
3. Uji flow end-to-end dengan akun uji dan data uji
4. Dokumentasikan hasil uji staging
5. Baru lanjut ke launch produksi

### Hasil audit staging execution saat ini
- Environment aktif sudah memiliki nilai untuk integrasi utama berikut:
  - `DATABASE_URL`
  - `FIREBASE_SERVICE_ACCOUNT_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `SMTP_SERVER`
  - `FROM_EMAIL`
  - `RAJAONGKIR_API_KEY`
  - `MIDTRANS_SERVER_KEY`
  - `MIDTRANS_CLIENT_KEY`
  - `REDIS_HOST`
- Variabel yang masih perlu dipastikan untuk staging/production final:
  - `PORT`
  - `APP_DEVELOPMENT`
  - `HOST_URL`
  - `MIDTRANS_IS_PRODUCTION`
- Smoke test publik terakhir pada environment lokal aktif:
  - `/docs` → `200`
  - `/openapi.json` → `200`
  - `/product/all` → `200`
  - `/brand/all` → `200`
  - `/type/all` → `200`

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
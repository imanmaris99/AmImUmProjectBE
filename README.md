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

EMAIL_PROVIDER=brevo_api
BREVO_API_KEY=
FROM_EMAIL=
SMTP_TIMEOUT_SECONDS=15

RAJAONGKIR_API_KEY=
RAJAONGKIR_API_HOST=rajaongkir.komerce.id
RAJAONGKIR_API_BASE_PATH=/api/v1

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

Untuk menjalankan aplikasi secara lokal dengan runtime yang lebih terkontrol:
```bash
poetry run python run.py
```

Atau mode development dengan reload:
```bash
poetry run uvicorn app.main:app --reload
```

Aplikasi akan berjalan di `http://127.0.0.1:8000`.

Catatan penting untuk QA lokal:
- Gunakan satu metode run saja dalam satu waktu
- Hindari menjalankan beberapa instance `uvicorn` bersamaan pada port yang sama
- Utamakan `poetry run python run.py` saat ingin verifikasi runtime yang lebih stabil
- Gunakan `uvicorn --reload` hanya saat memang sedang development aktif


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

Catatan penting untuk shipping cost Komerce:
- gunakan `RAJAONGKIR_API_HOST=rajaongkir.komerce.id`
- gunakan `RAJAONGKIR_API_BASE_PATH=/api/v1`
- jangan gunakan lagi endpoint lama `api.rajaongkir.com/starter/*` karena sudah nonaktif

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

## Deploy Readiness Minimum (Railway)

Jika backend akan dinaikkan ke Railway sebagai target staging atau awal production, gunakan acuan minimum berikut:

### Start command
- Railway dapat menjalankan aplikasi dengan command:

```bash
python run.py
```

### Environment minimum yang wajib dipastikan
- `PORT`
- `DATABASE_URL`
- `SECRET_KEY`
- `MIDTRANS_SERVER_KEY`
- `MIDTRANS_CLIENT_KEY`
- `MIDTRANS_IS_PRODUCTION`
- `RAJAONGKIR_API_KEY`
- `RAJAONGKIR_API_HOST=rajaongkir.komerce.id`
- `RAJAONGKIR_API_BASE_PATH=/api/v1`
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `FROM_EMAIL`

### Smoke test pasca deploy
- `GET /docs` -> harus `200`
- `GET /openapi.json` -> harus `200`
- `GET /product/all` -> harus `200`
- `GET /brand/all` -> harus `200`
- `GET /type/all` -> harus `200` dan mengembalikan contract variant list yang memuat `product_id`, `product`, `name`, `variant`, `expiration`, `stock`, `discount`, `discounted_price`, `img`, `updated_at`
- `POST /type/create` -> respons create variant harus minimal memuat `product_id`, `name`, `variant`, `expiration`, `stock`, `discount`, `created_at`, `updated_at`
- `PUT /type/{type_id}` -> respons update variant sebaiknya mengembalikan payload variant yang kaya agar dashboard mudah sinkron setelah update

### Catatan sebelum mengklaim production penuh
- pastikan hanya satu runtime app aktif
- jalankan migrasi database pada environment target
- verifikasi ulang flow checkout -> payment -> callback pada environment deploy
- jangan copy `.env` lokal mentah, isi ulang env Railway satu per satu dengan nilai yang benar

## Launch Readiness Backend Checklist

Status saat ini untuk kesiapan backend menuju staging/produksi:

### Yang sudah tervalidasi
- Aplikasi dapat dijalankan secara lokal
- Endpoint dokumentasi `/docs` -> `200`
- Endpoint OpenAPI `/openapi.json` -> `200`
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
- Uji register -> verify email -> login -> checkout -> payment secara end-to-end
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
- Flow `POST /user/register` saat ini sudah lolos validasi schema dan validasi password, tetapi masih gagal end-to-end jika kredensial SMTP aktif tidak diterima provider email (`535 Username and Password not accepted`)

### Rekomendasi langkah berikut
1. Siapkan environment staging final berdasarkan `.env.example`
2. Verifikasi kredensial SMTP aktif dan pastikan provider email menerima login aplikasi
   - jika memakai Gmail, gunakan `SMTP_SERVER=smtp.gmail.com`, `SMTP_PORT=587`
   - pastikan `SMTP_USER` sesuai akun pengirim
   - gunakan app password yang valid, bukan password login biasa
   - pastikan `FROM_EMAIL` sesuai identitas pengirim yang diizinkan
3. Jalankan migrasi database di staging
4. Uji flow end-to-end dengan akun uji dan data uji
5. Dokumentasikan hasil uji staging
6. Baru lanjut ke launch produksi

### Hasil audit staging execution saat ini
- QA runtime register terbaru:
  - payload register invalid password -> `400` dengan pesan validasi yang lebih jelas
  - payload register valid -> saat ini mentok di pengiriman email verifikasi karena SMTP login ditolak provider
  - koneksi SMTP ke `smtp.gmail.com:587` dan `STARTTLS` berhasil, tetapi `server.login(...)` gagal dengan `535 Username and Password not accepted`
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
  - `/docs` -> `200`
  - `/openapi.json` -> `200`
  - `/product/all` -> `200`
  - `/brand/all` -> `200`
  - `/type/all` -> `200`

### Checklist validasi manual flow staging

#### 1. Auth dan verifikasi email
- `POST /user/register`
  - siapkan email uji baru yang belum pernah terdaftar
  - verifikasi respons sukses `201`
  - verifikasi data user terbentuk di database
- `POST /user/verify-email`
  - gunakan kode verifikasi yang benar dari email/sistem
  - verifikasi user berubah menjadi terverifikasi/aktif
  - uji juga kode salah atau kedaluwarsa untuk memastikan error terkendali
- `POST /user/login`
  - uji login dengan akun yang sudah terverifikasi
  - simpan token login untuk pengujian endpoint terproteksi
  - uji kombinasi password salah untuk memastikan respons error sesuai
- `POST /user/auth/google-login`
  - hanya diuji jika Firebase token uji valid tersedia

#### 2. Payment dan notifikasi
- `POST /payments/create`
  - gunakan token login user valid
  - gunakan order yang memang valid dan dimiliki user
  - verifikasi transaksi Midtrans berhasil terbentuk
- `POST /payments/handler-notifications`
  - kirim payload notifikasi yang valid dari skenario sandbox/staging
  - verifikasi status payment dan order ikut ter-update
  - uji payload tidak valid untuk memastikan validation/error handling tetap aman

#### 3. Endpoint publik minimum
- `GET /docs`
- `GET /openapi.json`
- `GET /product/all`
- `GET /brand/all`
- `GET /type/all`

#### 4. Catatan eksekusi aman
- Jangan gunakan akun pelanggan riil untuk pengujian staging
- Gunakan data uji yang bisa dibersihkan atau ditelusuri
- Jangan commit `.env`, token, atau payload sensitif ke repo
- Simpan hasil uji per flow: input, output, status akhir, dan blocker jika ada

### Template pencatatan hasil QA staging

Gunakan format berikut setiap kali menjalankan validasi manual:

```markdown
#### [FLOW NAME]
- Endpoint:
- Method:
- Preconditions:
- Test data:
- Expected result:
- Actual result:
- Status: PASS / FAIL / BLOCKED
- Blocker / notes:
```

### Hasil QA dasar yang sudah tervalidasi
- `GET /docs`
  - Expected: dokumentasi API dapat dibuka
  - Actual: `200`
  - Status: PASS
- `GET /openapi.json`
  - Expected: schema OpenAPI tersedia
  - Actual: `200`
  - Status: PASS
- `GET /product/all`
  - Expected: daftar produk publik dapat diakses
  - Actual: `200`, payload produk berhasil diterima
  - Status: PASS
- `GET /brand/all`
  - Expected: daftar brand publik dapat diakses
  - Actual: `200`
  - Status: PASS
- `GET /type/all`
  - Expected: daftar tipe/variant publik dapat diakses
  - Actual: `200`
  - Status: PASS
- `POST /rajaongkir/shipping-cost`
  - Expected: kalkulasi ongkir domestic Komerce dapat dipanggil
  - Actual: `200`, daftar layanan ongkir valid berhasil diterima
  - Status: PASS
- `POST /payments/handler-notifications`
  - Expected: callback publik Midtrans dengan signature valid dapat diproses
  - Actual: `200`, status pembayaran berhasil diperbarui pada simulasi callback
  - Status: PASS

### Admin dashboard API readiness

Role resmi project saat ini:
- `owner` -> level tertinggi, pemilik toko
- `admin` -> operasional internal
- `customer` -> pembeli

Prinsip akses internal saat ini:
- endpoint panel internal dapat diakses oleh `admin` dan `owner`
- `customer` tidak boleh mengakses endpoint internal
- role `owner` adalah penerus penamaan singkat dari konsep `pemilik_toko`

Endpoint admin yang sudah siap dipakai untuk dashboard internal:

- `POST /admin/login`
- `GET /admin/orders`
- `GET /admin/orders/{order_id}`
- `PATCH /admin/orders/{order_id}/status`
- `GET /admin/payments`
- `GET /admin/payments/order/{order_id}`
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/status`
- `GET /admin/dashboard/summary`

Ringkasan metric dashboard admin saat ini mencakup:
- users:
  - `total_users`
  - `total_active_users`
- orders:
  - `total_orders`
  - `total_pending_orders`
  - `total_paid_orders`
  - `total_processing_orders`
  - `total_shipped_orders`
  - `total_completed_orders`
  - `total_cancelled_orders`
  - `total_failed_orders`
- payments:
  - `total_pending_payments`
  - `total_settlement_payments`
  - `total_expire_payments`
  - `total_cancel_payments`
  - `total_deny_payments`
  - `total_refund_payments`
  - `total_capture_payments`
- revenue:
  - `gross_revenue_paid_orders`

Catatan:
- Semua endpoint admin di atas membutuhkan token internal yang valid dengan role `admin` atau `owner`, kecuali `POST /admin/login`.
- Query filter yang sudah tersedia saat ini:
  - orders: `status`, `skip`, `limit`
    - allowed status: `pending`, `paid`, `processing`, `shipped`, `completed`, `cancelled`, `failed`, `capture`, `refund`
  - payments: `status`, `skip`, `limit`
    - allowed status: `pending`, `settlement`, `expire`, `cancel`, `deny`, `refund`, `capture`
  - users: `role`, `is_active`, `skip`, `limit`
    - allowed role saat ini di list admin backend: `admin`, `customer`
    - catatan policy project terbaru: role resmi global adalah `owner`, `admin`, `customer`
- Guard tambahan saat ini:
  - endpoint status user admin tidak dipakai untuk mengubah status akun yang role-nya `admin`
- Swagger untuk route admin sudah diberi summary/description dasar agar lebih mudah dipakai saat QA dan integrasi frontend admin.

### Frontend admin integration map

Role resmi yang dipakai frontend dan backend:
- `owner`
- `admin`
- `customer`

#### 1. Internal login
- Route login internal:
  - `POST /admin/login`
- Role yang boleh masuk panel internal:
  - `owner`
  - `admin`
- Role `customer` tidak boleh diarahkan ke dashboard internal.

#### 2. Dashboard owner/admin
Landing dashboard internal saat ini dapat memakai:
- `GET /admin/dashboard/summary`

Widget minimum yang siap dipakai:
- total users
- total active users
- total orders
- total pending orders
- total paid orders
- total processing orders
- total shipped orders
- total completed orders
- total cancelled orders
- total failed orders
- total pending payments
- total settlement payments
- total expire payments
- total cancel payments
- total deny payments
- total refund payments
- total capture payments
- gross revenue paid orders

#### 3. Order management screen
Endpoint yang siap dipakai:
- `GET /admin/orders`
- `GET /admin/orders/{order_id}`
- `PATCH /admin/orders/{order_id}/status`

Filter list yang siap:
- `status`
- `skip`
- `limit`

Allowed order status saat ini:
- `pending`
- `paid`
- `processing`
- `shipped`
- `completed`
- `cancelled`
- `failed`
- `capture`
- `refund`

#### 4. Payment monitoring screen
Endpoint yang siap dipakai:
- `GET /admin/payments`
- `GET /admin/payments/order/{order_id}`

Filter list yang siap:
- `status`
- `skip`
- `limit`

Allowed payment status saat ini:
- `pending`
- `settlement`
- `expire`
- `cancel`
- `deny`
- `refund`
- `capture`

#### 5. User management screen
Endpoint yang siap dipakai:
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/status`
  - policy terbaru: owner-only

Filter list yang siap:
- `role`
- `is_active`
- `skip`
- `limit`

Catatan penting user management saat ini:
- endpoint status user tidak dipakai untuk mengubah status akun internal level admin/owner
- list admin backend saat ini masih memvalidasi role filter `admin` dan `customer`
- policy project resmi tetap memakai 3 role: `owner`, `admin`, `customer`

#### 6. Navigasi frontend admin yang disarankan
Menu minimum internal panel:
- Dashboard
- Orders
- Payments
- Users

Pemisahan role yang disarankan di frontend:
- `owner`
  - lihat semua menu internal
  - disiapkan untuk menu strategis tambahan di fase berikutnya
- `admin`
  - lihat dashboard operasional, orders, payments, users
- `customer`
  - tidak boleh melihat menu internal

#### 7. Catatan implementasi frontend
- simpan token internal dari `POST /admin/login`
- gunakan guard route frontend berbasis role `owner` atau `admin`
- jangan tampilkan dashboard internal untuk `customer`
- siapkan ekstensi berikutnya untuk owner-only actions tanpa merusak panel admin operasional

### Role access matrix

#### A. Customer area
- Public catalog, brand, type, category, article:
  - guest/customer allowed
- Cart, wishlist, shipment address, shipment selection:
  - `customer`
- Checkout, payment create, my orders, my profile:
  - `customer`
- Customer hanya boleh mengakses resource miliknya sendiri.

#### B. Internal operational area
- Dashboard summary:
  - `admin`
  - `owner`
- Order management:
  - `admin`
  - `owner`
- Payment monitoring:
  - `admin`
  - `owner`
- User management operasional:
  - `admin`
  - `owner`
- Product, category, production, article, pack type management internal:
  - `admin`
  - `owner`

#### C. Owner-only area (policy target)
Area berikut disepakati sebagai owner-only secara policy project, walau sebagian implementasi endpoint spesifiknya masih perlu ditutup bertahap:
- pengelolaan akun admin/internal level tinggi
- perubahan role strategis user internal
- kontrol penuh atas akun `owner`
- keputusan sensitif yang memengaruhi struktur operasional internal

#### D. Forbidden matrix
- `customer` tidak boleh masuk panel internal
- `admin` tidak boleh diperlakukan setara penuh dengan `owner`
- endpoint sensitif level owner tidak boleh dibuka ke `customer`
- endpoint sensitif level owner tidak boleh dibuka otomatis ke seluruh `admin` tanpa review policy

#### E. Implementation direction
Prioritas implementasi berikutnya agar tetap konsisten:
1. pertahankan guard internal untuk `admin` dan `owner`
2. tambah guard owner-only saat endpoint strategis mulai dibuat
3. pisahkan menu frontend berdasarkan role hasil login
4. hindari hardcode akses yang menyamakan semua role internal
5. terapkan owner-only guard bertahap pada endpoint sensitif
   - saat ini `PATCH /admin/users/{user_id}/status` mulai dibatasi untuk `owner`

### Endpoint access audit summary

#### 1. Public / guest-first endpoints
Endpoint berikut secara fungsi produk cocok diperlakukan sebagai area publik sebelum login:
- katalog dan detail produk (`product_router` read endpoints)
- brand/type/category public listing
- article/news public listing
- RajaOngkir lookup dan shipping cost helper yang dipakai frontend checkout flow

#### 2. Customer-auth endpoints
Endpoint berikut cocok diperlakukan sebagai area customer setelah login:
- cart (`cart_router`)
- wishlist (`wishlist_router`)
- shipment address (`shipment_address_router`)
- shipment selection (`shipment_router`)
- courier selection (`courier_router`)
- checkout dan my orders (`order_router`)
- payment create untuk order customer (`payment_router` create flow)
- profile/update profile/password/photo (`user_router` self-service endpoints)
- rating product oleh customer (`rating_router`)

#### 3. Internal endpoints
Endpoint berikut cocok diperlakukan sebagai area internal untuk `admin` dan `owner`:
- `admin_router`
- create/update/delete article internal
- create/update category internal
- product management internal
- production management internal
- pack type management internal

#### 4. Owner-only policy candidates
Dari audit struktur saat ini, area berikut paling layak dipindahkan bertahap ke owner-only policy ketika endpoint spesifiknya mulai dipisah:
- perubahan role user internal
- pengelolaan akun admin/owner
- kontrol sensitif atas user internal level tinggi
- keputusan strategis yang mengubah struktur operasional internal

#### 5. Kesimpulan audit endpoint saat ini
- struktur global backend sudah mengarah ke 3 lapisan akses yang sehat:
  - public / guest
  - customer-auth
  - internal (`admin` + `owner`)
- guard internal utama sekarang sudah menerima `admin` dan `owner`
- customer flow tetap cocok dipertahankan seperti marketplace umum: login hanya diperlukan saat mulai memakai resource personal/transaksional
- langkah implementasi berikutnya sebaiknya fokus pada pemisahan lebih tegas antara internal-operational vs owner-only

### Frontend internal role-based screen map

#### 1. Public storefront layer
Screen publik tanpa login:
- Home / landing toko
- Product listing
- Product detail
- Brand / category / type exploration
- Article / news / info page

Tujuan:
- calon customer bisa eksplor tanpa hambatan login
- role belum dipakai untuk area ini

#### 2. Customer-auth layer
Screen customer setelah login:
- My account / profile
- Edit profile / password / photo
- Wishlist
- Cart
- Shipment address
- Shipment selection / courier selection
- Checkout
- My orders
- Payment follow-up
- Product rating

Prinsip:
- customer hanya melihat dan mengelola resource miliknya sendiri

#### 3. Internal shared layer (`admin` + `owner`)
Screen internal yang boleh dipakai oleh `admin` dan `owner`:
- Internal login
- Dashboard summary
- Order management list
- Order detail
- Payment monitoring list
- Payment detail by order
- User list
- User detail
- Product management
- Category management
- Article management
- Production / pack type management

Prinsip:
- fokus pada operasional harian
- layout dan navigation internal sebaiknya sama untuk `admin` dan `owner`

#### 4. Owner-only layer
Screen/aksi yang sebaiknya disiapkan sebagai owner-only:
- sensitive user control
- internal role control
- admin/owner management
- strategic settings and future high-risk actions

Status implementasi saat ini:
- owner-only action yang sudah mulai aktif di backend:
  - `PATCH /admin/users/{user_id}/status`

#### 5. UX/navigation recommendation
Sidebar internal minimum:
- Dashboard
- Orders
- Payments
- Users
- Catalog Management
- Content Management

Role-aware navigation:
- `owner`
  - lihat semua menu internal
  - owner-only action/button tampil
- `admin`
  - lihat menu operasional internal
  - owner-only action/button disembunyikan
- `customer`
  - tidak boleh melihat internal sidebar

#### 6. Frontend implementation notes
- pisahkan route group publik, customer-auth, dan internal
- simpan token internal terpisah secara jelas pada flow dashboard internal
- lakukan role check setelah login sebelum render internal menu
- jangan gunakan pendekatan satu layout untuk semua role tanpa filtering permission
- tandai action sensitif sejak awal agar owner-only mudah dirawat saat frontend membesar

### Auth dan payment QA execution prep

#### Contoh payload aman untuk register
```json
{
  "firstname": "Test",
  "lastname": "User",
  "gender": "male",
  "email": "staging-test@example.com",
  "phone": "+6281234567890",
  "password": "Test12345"
}
```

#### Contoh payload untuk verify email
```json
{
  "code": "123456",
  "email": "staging-test@example.com"
}
```

#### Contoh payload untuk login
```json
{
  "email": "staging-test@example.com",
  "password": "Test12345"
}
```

#### Contoh payload untuk create payment
```json
{
  "order_id": "replace-with-valid-order-id"
}
```

#### Contoh payload untuk handler notifications
```json
{
  "order_id": "replace-with-valid-order-id",
  "transaction_status": "settlement",
  "fraud_status": "accept",
  "payment_type": "bank_transfer",
  "gross_amount": "21000.00",
  "signature_key": "replace-with-valid-midtrans-signature"
}
```

#### Preconditions penting sebelum QA auth/payment
- Email test harus bisa diakses jika flow verifikasi memakai email nyata
- User test harus dibuat khusus untuk staging, bukan akun pelanggan riil
- Order test harus valid dan memang dimiliki user test
- Kredensial Midtrans/Firebase/SMTP harus sesuai environment yang sedang diuji
- Token login hanya dipakai sementara untuk sesi uji dan tidak disimpan ke repo

#### Blocker teknis yang perlu diingat
- `POST /payments/create` butuh user login valid dan order valid
- `POST /payments/handler-notifications` baru bermakna penuh jika ada transaksi/order yang memang sudah terbentuk
- `POST /user/auth/google-login` bergantung pada token Firebase/Google yang valid

### Hasil observasi stabilitas endpoint publik
- `GET /product/all`
  - Dilakukan 10 kali probe berturut-turut
  - Hasil akhir: stabil `200`
  - Catatan: belum ada bukti gagal konsisten pada observasi ini
- `GET /brand/all`
  - Dilakukan 10 kali probe berturut-turut
  - Hasil akhir: stabil `200`
  - Setelah patch konsistensi response, message tervalidasi menjadi seragam: `All list of brands can accessed successfully`
- `GET /type/all`
  - Dilakukan 10 kali probe berturut-turut
  - Hasil akhir: stabil `200`

### Catatan runtime verification
- Saat verifikasi restart-aware, terdeteksi dua proses `uvicorn` aktif dengan interpreter berbeda
- Kondisi ini berisiko membuat hasil QA lokal membingungkan karena request bisa tidak selalu merepresentasikan runtime yang benar-benar diharapkan
- Untuk staging/production, jalankan hanya satu instance aplikasi yang terkontrol agar hasil verifikasi lebih dapat dipercaya
- Untuk QA lokal, hindari mencampur interpreter global Python dan interpreter `.venv` project pada runtime yang sama
- Endpoint shipping cost lama `api.rajaongkir.com/starter/*` sudah nonaktif, gunakan host `rajaongkir.komerce.id` dengan base path `/api/v1`
- Flow courier dan shipment sekarang mengasumsikan satu record aktif per user, create baru akan menonaktifkan pilihan aktif sebelumnya
- Masih ada warning relasi SQLAlchemy pada area shipment/address (`SAWarning: Multiple rows returned with uselist=False`) yang perlu dibersihkan sebelum menyatakan production full-clean

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

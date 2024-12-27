from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import scheduler untuk penghapusan user yang belum diverifikasi
from app.utils.scheduler import start_scheduler

# Import semua router dari controller
from app import controllers

# Inisialisasi aplikasi FastAPI
app = FastAPI(
    title="Dokumentasi API -> App. AmImUm Herbal",  
    description="Media API untuk mengelola serta melakukan testing CRUD pada proyek App. AmImUm Herbal",
    version="1.0.0",
    terms_of_service="https://github.com/imanmaris99/AmImUmProjectBE",
    contact={
        "name": "Developer API",
        "url": "https://github.com/imanmaris99",
        "email": "herbalamimum99@gmail.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Middleware untuk menangani CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "https://imanmaris-portfolio.vercel.app",
    "https://tools.slingacademy.com",
    "https://www.slingacademy.com",
    "https://amimumherbalproject.vercel.app",
    "https://amimumherbalproject-git-staging-imanmaris99s-projects.vercel.app",
    "https://api.sandbox.midtrans.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=['*'],
)

# Mount directory untuk akses gambar statis
root_directory = os.getcwd()  # Mendapatkan direktori kerja saat ini
images_directory = os.path.join(root_directory, "images")
app.mount("/images", StaticFiles(directory=images_directory), name="images")

# Event startup
@app.on_event("startup")
async def startup_event():
    # Memulai scheduler untuk menghapus user yang belum diverifikasi
    start_scheduler()

# Menyertakan semua router
app.include_router(controllers.admin_router.router)
app.include_router(controllers.user_router.router)
app.include_router(controllers.article_router.router)
app.include_router(controllers.category_router.router)
app.include_router(controllers.production_router.router)
app.include_router(controllers.product_router.router)
app.include_router(controllers.pack_type_router.router)
app.include_router(controllers.rating_router.router)
app.include_router(controllers.wishlist_router.router)
app.include_router(controllers.cart_router.router)
app.include_router(controllers.courier_router.router)
app.include_router(controllers.shipment_address_router.router)
app.include_router(controllers.shipment_router.router)
app.include_router(controllers.order_router.router)
app.include_router(controllers.payment_router.router)
app.include_router(controllers.rajaongkir_router.router)

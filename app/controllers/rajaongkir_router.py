from fastapi import APIRouter, Depends
from typing import List
from app.services.rajaongkir_services import get_province_data, get_city_data, get_shipping_cost
from app.dtos.rajaongkir_dtos import ProvinceDto, CityDto, ShippingCostRequest, ShippingCostDto
from app.utils.optional import build


router = APIRouter(
    prefix="/rajaongkir",
    tags=["ThirdParty/ RajaOngkir"]
)

@router.get("/provinces", response_model=List[ProvinceDto])
def fetch_provinces():
    """Mengambil semua data provinsi."""
    result = get_province_data()
    return result.unwrap()

@router.get("/cities", response_model=List[CityDto])
def fetch_cities():
    """Mengambil semua data kota."""
    result = get_city_data()
    return result.unwrap()

@router.post(
        "/shipping-cost", 
        response_model=ShippingCostDto
        )
def read_shipping_cost(request: ShippingCostRequest):
    """
    Endpoint ini digunakan untuk menghitung ongkos kirim berdasarkan beberapa parameter seperti:
    
    - `origin`: ID atau nama kota/kabupaten asal pengiriman. Misal: id= 497 (untuk id kota Wonogiri).
    - `destination`: ID atau nama kota/kabupaten tujuan pengiriman. Misal: id= 455 (untuk id kota Tangerang).
    - `weight`: Berat barang dalam gram. Default 1000 gram (1 kg). Masukkan angka sesuai berat yang sebenarnya.
    - `courier`: Nama kurir yang digunakan. Pilih dari salah satu: 'jne', 'pos', atau 'tiki'. Default: 'jne'.
    
    Response yang diterima akan berisi estimasi ongkos kirim berdasarkan input yang diberikan.
    """
    
    # Catatan tambahan untuk pengguna route:
    # - Pastikan ID kota asal dan tujuan sesuai dengan database kota yang digunakan.
    # - Berat barang harus dalam satuan gram.
    # - Pilih salah satu kurir yang tersedia (jne, pos, tiki).
    
    result = get_shipping_cost(
        request_data=request
    )    
        
    if result.error:
        raise result.error
    
    return result.unwrap()  
# Backend Hardening Checklist

Fokus dokumen ini sengaja sempit, hanya untuk tindak lanjut audit backend saat ini.

## 1. Auth
- [x] Hentikan login password yang terlihat seolah diverifikasi oleh Firebase padahal tidak.
- [x] Pastikan login password hanya memakai hash password lokal.
- [ ] Putuskan strategi auth final, full local auth atau full Firebase token verification.
- [ ] Tambahkan refresh token atau session strategy yang jelas jika memang dibutuhkan.
- [ ] Tambahkan rate limiting untuk login dan reset password.
- [ ] Tambahkan audit log untuk login gagal, login sukses admin, dan reset password.

## 2. Payment callback
- [x] Tetapkan callback Midtrans publik sebagai flow utama.
- [x] Tandai endpoint lama internal sebagai deprecated.
- [ ] Hapus endpoint callback lama setelah semua client internal berhenti memakainya.
- [ ] Tambahkan replay protection atau idempotency check untuk callback yang sama.
- [ ] Pastikan semua perubahan status order dari payment punya rule transisi yang jelas.
- [ ] Tambahkan audit log untuk callback valid, invalid signature, dan payment status changes.

## 3. Logging dan debug hygiene
- [x] Hapus print debug dari flow auth, payment, dan upload yang disentuh.
- [ ] Standarkan logger format dan level log per environment.
- [ ] Pastikan log tidak membocorkan token, secret, email sensitif, atau payload penuh dari payment provider.
- [ ] Pisahkan log debug development dan error production.

## 4. Config dan environment
- [ ] Pindahkan daftar CORS origin ke environment variable.
- [ ] Validasi env wajib saat startup dengan pesan error yang jelas.
- [ ] Pisahkan env development, staging, dan production dengan tegas.
- [ ] Review semua credential provider agar tidak pernah fallback ke nilai dummy di production.

## 5. Testing minimum wajib
- [ ] Test login sukses user aktif.
- [ ] Test login gagal karena password salah.
- [ ] Test login gagal untuk akun nonaktif.
- [ ] Test callback Midtrans gagal jika signature tidak valid.
- [ ] Test callback Midtrans sukses mengubah status payment dan order.
- [ ] Test endpoint deprecated masih kompatibel sampai flow lama benar-benar dihapus.

## 6. Setelah checklist ini
Prioritas berikutnya tetap sempit:
1. selesaikan test auth dan payment callback
2. pindahkan CORS ke env
3. rapikan scheduler agar aman untuk multi-instance production

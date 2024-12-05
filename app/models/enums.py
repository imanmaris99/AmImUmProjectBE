from enum import Enum


# Enum untuk tipe pembayaran yang valid
class PaymentTypeEnum(str, Enum):
    credit_card = "credit_card"
    gopay = "gopay"
    bank_transfer = "bank_transfer"
    alfamart = "alfamart"
    shopeepay = "shopeepay"
    # Tambahkan tipe pembayaran lain sesuai yang disediakan oleh Midtrans

    @classmethod
    def load_from_midtrans(cls):
        """
        Mengambil daftar tipe pembayaran yang valid dari API Midtrans.
        Biasanya Anda perlu memanggil API untuk mendapatkan data ini.
        Untuk saat ini, kita hanya mengembalikan nilai-nilai dari Enum.
        """
        return [method.value for method in cls]

class DeliveryTypeEnum(str, Enum):
    delivery = "delivery"
    pickup = "pickup"

# Enum untuk status transaksi pembayaran
class TransactionStatusEnum(str, Enum):
    pending = "pending"
    settlement = "settlement"
    expire = "expire"
    cancel = "cancel"
    deny = "deny"
    refund = "refund"
    capture = "capture"  # Tambahkan status ini

# Enum untuk status fraud transaksi pembayaran
class FraudStatusEnum(str, Enum):
    accept = "accept"
    challenge = "challenge"
    deny = "deny"


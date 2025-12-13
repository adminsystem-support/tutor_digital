from app import app
from datetime import timedelta

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def format_rupiah(value):
    """Memformat angka menjadi string Rupiah (misal: 99.000)"""
    return "{:,.0f}".format(value).replace(",", ".")

def adjust_timezone(dt, hours=7):
    """Menyesuaikan waktu UTC ke waktu lokal (misal: WIB = +7 jam)"""
    if dt:
        return dt + timedelta(hours=hours)
    return dt
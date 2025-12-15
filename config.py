import os

# Mendapatkan path absolut dari direktori saat ini
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Kunci rahasia untuk keamanan sesi dan formulir
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ganti-dengan-kunci-rahasia-yang-sulit'
    
    # --- KONFIGURASI DATABASE SQLITE (UNTUK PYTHONANYWHERE) ---
    # Jika variabel lingkungan DATABASE_URL tidak ada, gunakan SQLite lokal
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
        
    # Catatan: Jika Anda ingin kembali ke PostgreSQL, gunakan format ini:
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    #     'postgresql://postgres:Triniti%402025@localhost:5432/jago_kursus'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- KONFIGURASI UPLOAD ---
    UPLOAD_FOLDER = 'static/proofs'
    IMAGE_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
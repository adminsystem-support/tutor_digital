import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ganti-dengan-kunci-rahasia-yang-sulit'
    
    # --- KONFIGURASI DATABASE POSTGRESQL ---
    # Format: postgresql://user:password@host:port/database_name
    # Ganti 'user', 'password', dan 'database_name' dengan yang Anda buat saat instalasi.
    # Contoh: postgresql://postgres:kata_sandi_anda@localhost:5432/db_aplikasi_web
    
    # URI DATABASE YANG SUDAH DIUPDATE:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:Triniti%402025@localhost:5432/jago_kursus'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- KONFIGURASI UPLOAD ---
    UPLOAD_FOLDER = 'static/proofs'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
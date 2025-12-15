from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os 
from datetime import datetime

# Import konfigurasi
from config import Config

# --- 1. INISIALISASI APLIKASI ---
app = Flask(__name__)
app.config.from_object(Config)

# --- CONTEXT PROCESSOR (Untuk membuat variabel tersedia di semua template) ---
@app.context_processor
def inject_global_variables():
    """Membuat fungsi dan variabel global tersedia di semua template."""
    return dict(
        now=datetime.utcnow # Menggunakan UTC, atau datetime.now() jika Anda yakin dengan timezone server
    )

# --- INISIALISASI EKSTENSI ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

# --- IMPORT UTILS UNTUK FILTER JINJA ---
# Pastikan Anda sudah membuat file utils.py
from utils import format_rupiah, adjust_timezone 

# Daftarkan filter ke aplikasi
app.jinja_env.filters['format_rupiah'] = format_rupiah
app.jinja_env.filters['adjust_timezone'] = adjust_timezone

# --- IMPORT MODEL DAN ROUTES ---
# Import model agar Flask-Migrate dapat menemukannya
from models import User, Course, Lesson, Enrollment, LessonProgress 
# Import routes agar Flask tahu fungsi mana yang harus dijalankan
import routes 

# --- JIKA ANDA INGIN MENJALANKAN APLIKASI LANGSUNG DARI app.py ---
if __name__ == '__main__':
    # Pastikan folder IMAGE_FOLDER ada
    image_path = os.path.join(app.root_path, app.config['IMAGE_FOLDER'])
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    
    # Pastikan folder PROOF_FOLDER ada
    proof_path = os.path.join(app.root_path, app.config['PROOF_FOLDER'])
    if not os.path.exists(proof_path):
        os.makedirs(proof_path)
        
    app.run(debug=True)
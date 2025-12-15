from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional
from flask_wtf.file import FileField, FileAllowed
from models import User # Import model User

# --- FORMULIR ---

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    is_admin = BooleanField('Berikan Hak Akses Admin')
    full_name = StringField('Nama Lengkap')
    whatsapp_number = StringField('Nomor WhatsApp')
    submit = SubmitField('Buat Akun')

    # Validasi unik hanya untuk username
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Nama pengguna ini sudah digunakan.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ingat Saya')
    submit = SubmitField('Masuk')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Ulangi Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Daftar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Nama pengguna ini sudah digunakan.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email ini sudah terdaftar.')

class CourseForm(FlaskForm):
    title = StringField('Judul Kursus', validators=[DataRequired()])
    description = TextAreaField('Deskripsi', validators=[DataRequired()])
    
    category = SelectField('Kategori Kursus', 
                           choices=[
                               ('Web Dev', 'Web Dev'),
                               ('Data Science', 'Data Science'),
                               ('Desain Grafis', 'Desain Grafis'),
                               ('Jaringan', 'Jaringan'),
                               ('Office', 'Office'),
                               ('Umum', 'Umum')
                           ], 
                           validators=[DataRequired()])
    
    instructor_name = StringField('Nama Instruktur', validators=[DataRequired()])
    instructor_title = StringField('Jabatan Instruktur')
    rating = FloatField('Rating (Contoh: 4.8)', validators=[DataRequired()])
    price = IntegerField('Harga Normal (Rp)', validators=[DataRequired()])
    discount_percent = IntegerField('Diskon (%)', default=0)
    duration_hours = IntegerField('Durasi Kursus (Jam)', validators=[DataRequired()], default=10) # FIELD BARU
    
    image = FileField('Gambar Kursus', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Hanya file gambar (JPG, PNG, JPEG) yang diizinkan!'),
        Optional()
    ])
    
    instructor_image = FileField('Foto Instruktur', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Hanya file gambar (JPG, PNG, JPEG) yang diizinkan!'),
        Optional()
    ])
    
    submit = SubmitField('Simpan Perubahan')

class LessonForm(FlaskForm):
    title = StringField('Judul Pelajaran', validators=[DataRequired()])
    content = TextAreaField('Konten Pelajaran (Bisa HTML/Embed)', validators=[DataRequired()])
    order = IntegerField('Urutan Pelajaran', validators=[DataRequired()])
    duration_minutes = IntegerField('Durasi Pelajaran (Menit)', validators=[DataRequired()], default=15) # FIELD BARU
    submit = SubmitField('Tambah Pelajaran')

class ProfileForm(FlaskForm):
    full_name = StringField('Nama Lengkap (Untuk Sertifikat)', validators=[DataRequired()])
    whatsapp_number = StringField('Nomor WhatsApp (Contoh: 6281234567890)', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Simpan Perubahan Profil')
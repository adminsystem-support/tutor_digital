from app import app, db # HANYA app dan db dari app.py
from utils import allowed_file # <--- Ambil allowed_file dari utils.py
from models import User, Course, Lesson, Enrollment, LessonProgress
from forms import LoginForm, RegistrationForm, CourseForm, LessonForm, ProfileForm
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from functools import wraps
from werkzeug.utils import secure_filename
import os
from utils import allowed_file
from forms import AdminUserForm

# --- FUNGSI PEMBANTU ---

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Akses ditolak. Anda harus menjadi Administrator.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- 5. ROUTES (VIEWS) ---

@app.route('/')
@app.route('/index')
def index():
    courses = Course.query.all()
    return render_template('index.html', title='Beranda', courses=courses)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Username atau password tidak valid', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', title='Masuk', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Selamat, Anda sekarang terdaftar sebagai pengguna! Silakan masuk.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Daftar', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    enrollments = current_user.enrollments.all()
    
    user_courses = []
    for enrollment in enrollments:
        course = enrollment.course
        progress = course.get_progress(current_user.id)
        user_courses.append({'course': course, 'progress': progress})
        
    return render_template('dashboard.html', title='Dashboard Saya', user_courses=user_courses)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Cek apakah email diubah dan sudah digunakan oleh orang lain
        if form.email.data != current_user.email:
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None:
                flash('Email ini sudah terdaftar. Gunakan email lain.', 'danger')
                return redirect(url_for('profile'))
        
        # Simpan perubahan
        current_user.full_name = form.full_name.data
        current_user.whatsapp_number = form.whatsapp_number.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profil Anda berhasil diperbarui!', 'success')
        return redirect(url_for('profile'))
        
    elif request.method == 'GET':
        # Isi formulir dengan data saat ini
        form.full_name.data = current_user.full_name
        form.whatsapp_number.data = current_user.whatsapp_number
        form.email.data = current_user.email
        
    # Tambahkan data sertifikat (simulasi)
    completed_courses = []
    for enrollment in current_user.enrollments.all():
        course = enrollment.course
        if course.get_progress(current_user.id) == 100:
            completed_courses.append(course)
            
    return render_template('profile.html', 
                           title='Profil Saya', 
                           form=form,
                           completed_courses=completed_courses)

@app.route('/course/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = course.lessons.order_by(Lesson.order).all()
    
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    
    is_enrolled = enrollment.is_confirmed if enrollment else False
    
    payment_status = 'none'
    if enrollment:
        if enrollment.is_confirmed:
            payment_status = 'confirmed'
        elif enrollment.is_paid:
            payment_status = 'paid_pending'
        else:
            payment_status = 'unpaid'
    
    return render_template('course_detail.html', 
                           title=course.title, 
                           course=course, 
                           lessons=lessons, 
                           is_enrolled=is_enrolled,
                           payment_status=payment_status)

@app.route('/enroll/<int:course_id>')
@login_required
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    
    if course.price > 0:
        flash(f'Kursus "{course.title}" adalah kursus berbayar. Silakan selesaikan pembayaran.', 'info')
        return redirect(url_for('checkout', course_id=course_id))
    
    if Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first():
        flash(f'Anda sudah terdaftar di kursus {course.title}.', 'warning')
    else:
        # Untuk kursus gratis, langsung set is_paid=True dan is_confirmed=True
        enrollment = Enrollment(user_id=current_user.id, course_id=course_id, is_paid=True, is_confirmed=True)
        db.session.add(enrollment)
        db.session.commit()
        flash(f'Selamat! Anda berhasil terdaftar di kursus {course.title} (GRATIS).', 'success')
        
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/lesson/<int:lesson_id>')
@login_required
def lesson_view(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=lesson.course_id).first()
    is_enrolled = enrollment.is_confirmed if enrollment else False
    
    if not is_enrolled:
        flash('Anda harus terdaftar di kursus ini untuk melihat pelajaran.', 'danger')
        return redirect(url_for('course_detail', course_id=lesson.course_id))
        
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    is_completed = progress.is_completed if progress else False
    
    prev_lesson = Lesson.query.filter_by(course_id=lesson.course_id).filter(Lesson.order < lesson.order).order_by(Lesson.order.desc()).first()
    next_lesson = Lesson.query.filter_by(course_id=lesson.course_id).filter(Lesson.order > lesson.order).order_by(Lesson.order).first()
        
    return render_template('lesson_view.html', 
                           title=lesson.title, 
                           lesson=lesson, 
                           is_completed=is_completed,
                           prev_lesson=prev_lesson,
                           next_lesson=next_lesson,
                           Lesson=Lesson)

@app.route('/complete_lesson/<int:lesson_id>')
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=lesson.course_id).first()
    is_enrolled = enrollment.is_confirmed if enrollment else False
    
    if not is_enrolled:
        flash('Anda harus terdaftar di kursus ini.', 'danger')
        return redirect(url_for('course_detail', course_id=lesson.course_id))
        
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson_id).first()
    if progress is None:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson_id, is_completed=True)
        db.session.add(progress)
        flash(f'Pelajaran "{lesson.title}" ditandai sebagai selesai!', 'success')
    elif not progress.is_completed:
        progress.is_completed = True
        flash(f'Pelajaran "{lesson.title}" ditandai sebagai selesai!', 'success')
    else:
        flash(f'Pelajaran "{lesson.title}" sudah selesai.', 'info')
        
    db.session.commit()
    
    next_lesson = Lesson.query.filter_by(course_id=lesson.course_id).filter(Lesson.order > lesson.order).order_by(Lesson.order).first()
    
    if next_lesson:
        return redirect(url_for('lesson_view', lesson_id=next_lesson.id))
    else:
        flash('Selamat! Anda telah menyelesaikan semua pelajaran di kursus ini!', 'success')
        return redirect(url_for('course_detail', course_id=lesson.course_id))

@app.route('/courses/<category_name>')
def courses_by_category(category_name):
    courses = Course.query.filter_by(category=category_name).all()
    
    categories = [
        {'name': 'Web Dev', 'icon': 'code-slash', 'color': 'primary'},
        {'name': 'Data Science', 'icon': 'graph-up', 'color': 'success'},
        {'name': 'Desain Grafis', 'icon': 'palette', 'color': 'danger'},
        {'name': 'Jaringan', 'icon': 'router', 'color': 'info'},
        {'name': 'Office', 'icon': 'file-earmark-text', 'color': 'warning'}
    ]
    
    return render_template('courses_by_category.html', 
                           title=f'Kursus {category_name}', 
                           courses=courses, 
                           category_name=category_name,
                           categories=categories)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    kelas = request.args.get('kelas', '')
    
    search_filter = Course.title.ilike(f'%{query}%')
    
    if kelas:
        kelas_filter = Course.category.ilike(f'%{kelas}%')
        courses = Course.query.filter(search_filter, kelas_filter).all()
    else:
        courses = Course.query.filter(search_filter).all()
        
    categories = [
        {'name': 'Web Dev', 'icon': 'code-slash', 'color': 'primary'},
        {'name': 'Data Science', 'icon': 'graph-up', 'color': 'success'},
        {'name': 'Desain Grafis', 'icon': 'palette', 'color': 'danger'},
        {'name': 'Jaringan', 'icon': 'router', 'color': 'info'},
        {'name': 'Office', 'icon': 'file-earmark-text', 'color': 'warning'}
    ]
    
    return render_template('search_results.html', 
                           title=f'Hasil Pencarian: {query}', 
                           courses=courses, 
                           query=query,
                           selected_kelas=kelas,
                           categories=categories)

@app.route('/course/<int:course_id>/search', methods=['GET'])
@login_required
def search_lesson(course_id):
    course = Course.query.get_or_404(course_id)
    query = request.args.get('q', '')
    
    if not query:
        flash('Masukkan kata kunci untuk mencari pelajaran.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))

    lessons = Lesson.query.filter(
        Lesson.course_id == course_id,
        Lesson.title.ilike(f'%{query}%') | Lesson.content.ilike(f'%{query}%')
    ).order_by(Lesson.order).all()
    
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    is_enrolled = enrollment.is_confirmed if enrollment else False
    
    return render_template('course_detail.html', 
                           title=f'Hasil Pencarian di {course.title}', 
                           course=course, 
                           lessons=lessons, 
                           is_enrolled=is_enrolled,
                           search_query=query)

@app.route('/checkout/<int:course_id>')
@login_required
def checkout(course_id):
    course = Course.query.get_or_404(course_id)
    
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if enrollment and enrollment.is_confirmed:
        flash(f'Anda sudah terdaftar di kursus {course.title}.', 'warning')
        return redirect(url_for('course_detail', course_id=course_id))
        
    final_price = course.final_price # Menggunakan hybrid_property
    snap_token = "SIMULASI_SNAP_TOKEN_12345" 
    
    checkout_data = {
        'course': course,
        'final_price': final_price,
        'snap_token': snap_token,
        'user': current_user
    }
    
    return render_template('checkout.html', title='Pembayaran', data=checkout_data)

@app.route('/confirm_payment_upload/<int:course_id>', methods=['POST'])
@login_required
def confirm_payment_upload(course_id):
    course = Course.query.get_or_404(course_id)
    
    # 1. Ambil data formulir
    payment_method = request.form.get('payment_method')
    unique_code = request.form.get('unique_code')
    
    # 2. Validasi Metode Pembayaran
    if not payment_method:
        flash('Pilih salah satu metode pembayaran.', 'danger')
        return redirect(url_for('checkout', course_id=course_id))

    # 3. Validasi File Upload
    if 'proof_file' not in request.files:
        flash('Bukti pembayaran wajib diunggah.', 'danger')
        return redirect(url_for('checkout', course_id=course_id))
        
    file = request.files['proof_file']
    
    if file.filename == '' or not allowed_file(file.filename):
        flash('File bukti pembayaran tidak valid (hanya PNG, JPG, JPEG, PDF).', 'danger')
        return redirect(url_for('checkout', course_id=course_id))

    # 4. Proses Upload File (DEFINISIKAN FILENAME DI SINI)
    # Menggunakan app.config untuk UPLOAD_FOLDER
    upload_folder = app.config['UPLOAD_FOLDER']
    
    filename = secure_filename(f"{current_user.id}_{course_id}_{os.urandom(4).hex()}_{file.filename}")
    file_path = os.path.join(upload_folder, filename)
    
    # Pastikan folder upload ada
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    file.save(file_path) # File disimpan

    # 5. Simpan ke Database
    enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    
    # Hitung harga final (untuk WA blast)
    final_price = course.final_price # Menggunakan hybrid_property
    final_price_with_code = final_price + int(unique_code)
    
    if not enrollment:
        enrollment = Enrollment(
            user_id=current_user.id, 
            course_id=course_id, 
            is_paid=True, 
            is_confirmed=False,
            payment_method=payment_method,
            proof_of_payment=filename, # Gunakan filename yang baru diupload
            unique_code=int(unique_code) # <-- SIMPAN KODE UNIK
        )
        db.session.add(enrollment)
    else:
        # Jika enrollment sudah ada, update status dan bukti bayar
        enrollment.is_paid = True
        enrollment.is_confirmed = False
        enrollment.payment_method = payment_method
        enrollment.proof_of_payment = filename # Gunakan filename yang baru diupload
        enrollment.unique_code = int(unique_code) # <-- SIMPAN KODE UNIK
        
    db.session.commit()
    
    # 6. SIMULASI BLAST NOTIFIKASI WHATSAPP KE ADMIN
    admin_phone = "+6285715524962"
    message = (
        f"🔔 NOTIFIKASI PEMBAYARAN BARU 🔔\n"
        f"Kursus: {course.title}\n"
        f"Oleh: {current_user.username} ({current_user.email})\n"
        f"Total Bayar: Rp {final_price_with_code:,.0f} (Termasuk Kode Unik: {unique_code})\n"
        f"Status: Menunggu Verifikasi Admin.\n"
        f"Link Verifikasi: {url_for('admin_enrollments', _external=True)}"
    )
    
    print("="*50)
    print(f"SIMULASI WHATSAPP BLAST KE ADMIN ({admin_phone}):")
    print(message)
    print("="*50)
    
    flash(f'Konfirmasi pembayaran berhasil dikirim! Admin akan memverifikasi dalam 1x24 jam. Akses kursus akan terbuka setelah verifikasi.', 'success')
    return redirect(url_for('course_detail', course_id=course_id))


# --- ROUTES ADMIN ---

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    total_confirmed = Enrollment.query.filter_by(is_confirmed=True).count()
    
    return render_template('admin/dashboard.html', 
                           title='Admin Dashboard',
                           total_users=total_users,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           total_confirmed=total_confirmed,
                           Enrollment=Enrollment)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', title='Manajemen Pengguna', users=users)

@app.route('/admin/toggle_admin/<int:user_id>')
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Anda tidak bisa mengubah status admin Anda sendiri.', 'danger')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Status admin untuk {user.username} diubah menjadi {user.is_admin}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/courses')
@login_required
@admin_required
def admin_courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', title='Kelola Kursus', courses=courses)

@app.route('/admin/user_detail/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    
    enrollments = user.enrollments.all()
    
    user_courses = []
    for enrollment in enrollments:
        course = enrollment.course
        progress = course.get_progress(user.id)
        user_courses.append({'course': course, 'progress': progress})
        
    return render_template('admin/user_detail.html', 
                           title=f'Detail Pengguna: {user.username}', 
                           target_user=user, 
                           user_courses=user_courses)

@app.route('/admin/add_course', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            title=form.title.data, 
            description=form.description.data,
            category=form.category.data,
            instructor_name=form.instructor_name.data,
            instructor_title=form.instructor_title.data,
            rating=form.rating.data,
            price=form.price.data,
            discount_percent=form.discount_percent.data,
            image_url=form.image_url.data,
            instructor_image_url=form.instructor_image_url.data
        )
        db.session.add(course)
        db.session.commit()
        flash('Kursus baru berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_courses'))
        
    return render_template('admin/add_course.html', title='Tambah Kursus Baru', form=form)

@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm()
    
    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.category = form.category.data
        course.instructor_name = form.instructor_name.data
        course.instructor_title = form.instructor_title.data
        course.rating = form.rating.data
        course.price = form.price.data
        course.discount_percent = form.discount_percent.data
        course.image_url = form.image_url.data
        course.instructor_image_url = form.instructor_image_url.data
        
        db.session.commit()
        flash(f'Kursus "{course.title}" berhasil diperbarui!', 'success')
        return redirect(url_for('admin_courses'))
    
    elif request.method == 'GET':
        form.title.data = course.title
        form.description.data = course.description
        form.category.data = course.category
        form.instructor_name.data = course.instructor_name
        form.instructor_title.data = course.instructor_title
        form.rating.data = course.rating
        form.price.data = course.price
        form.discount_percent.data = course.discount_percent
        form.image_url.data = course.image_url
        form.instructor_image_url.data = course.instructor_image_url
        
    return render_template('admin/edit_course.html', 
                           title=f'Edit Kursus: {course.title}', 
                           form=form, 
                           course=course,
                           Lesson=Lesson)

@app.route('/admin/add_lesson/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_lesson(course_id):
    course = Course.query.get_or_404(course_id)
    form = LessonForm()
    
    if form.validate_on_submit():
        lesson = Lesson(
            course_id=course.id,
            title=form.title.data,
            content=form.content.data,
            order=form.order.data
        )
        db.session.add(lesson)
        db.session.commit()
        flash(f'Pelajaran "{lesson.title}" berhasil ditambahkan ke kursus {course.title}!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
        
    return render_template('admin/add_lesson.html', title=f'Tambah Pelajaran untuk {course.title}', form=form, course=course)

@app.route('/admin/edit_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course = lesson.course
    form = LessonForm()
    
    if form.validate_on_submit():
        lesson.title = form.title.data
        lesson.content = form.content.data
        lesson.order = form.order.data
        db.session.commit()
        flash(f'Pelajaran "{lesson.title}" berhasil diperbarui!', 'success')
        return redirect(url_for('course_detail', course_id=course.id))
        
    elif request.method == 'GET':
        form.title.data = lesson.title
        form.content.data = lesson.content
        form.order.data = lesson.order
        
    return render_template('admin/edit_lesson.html', title=f'Edit Pelajaran: {lesson.title}', form=form, course=course, lesson=lesson)

@app.route('/admin/delete_lesson/<int:lesson_id>', methods=['POST'])
@login_required
@admin_required
def delete_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    
    LessonProgress.query.filter_by(lesson_id=lesson.id).delete(synchronize_session=False)
    
    db.session.delete(lesson)
    db.session.commit()
    
    flash(f'Pelajaran "{lesson.title}" berhasil dihapus.', 'success')
    return redirect(url_for('course_detail', course_id=course_id))

@app.route('/admin/enrollments')
@login_required
@admin_required
def admin_enrollments():
    pending_enrollments_raw = Enrollment.query.filter_by(is_paid=True, is_confirmed=False).all()
    
    pending_enrollments = []
    for enrollment in pending_enrollments_raw:
        course = enrollment.course
        final_price = course.final_price # Menggunakan hybrid_property
        
        pending_enrollments.append({
            'enrollment': enrollment,
            'final_price': final_price
        })
    
    all_enrollments = Enrollment.query.all()
    
    return render_template('admin/enrollments.html', 
                           title='Manajemen Pendaftaran',
                           pending_enrollments=pending_enrollments,
                           all_enrollments=all_enrollments)

@app.route('/admin/confirm_enrollment/<int:enrollment_id>')
@login_required
@admin_required
def admin_confirm_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    if enrollment.is_paid:
        enrollment.is_confirmed = True
        db.session.commit()
        flash(f'Pendaftaran untuk {enrollment.student.username} di kursus {enrollment.course.title} berhasil dikonfirmasi!', 'success')
    else:
        flash('Pendaftaran ini belum ditandai sebagai sudah dibayar.', 'danger')
        
    return redirect(url_for('admin_enrollments'))

@app.route('/admin/enrollment_detail/<int:enrollment_id>')
@login_required
@admin_required
def admin_enrollment_detail(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    course = enrollment.course
    
    # Nominal yang diharapkan TANPA kode unik
    expected_price = course.final_price # Menggunakan hybrid_property
    
    # --- FIX: Pastikan unique_code adalah integer, gunakan 0 jika None ---
    unique_code_value = enrollment.unique_code if enrollment.unique_code is not None else 0
    
    # Nominal yang DIBAYAR (termasuk kode unik)
    paid_price = expected_price + unique_code_value
    
    return render_template('admin/enrollment_detail.html',
                           title=f'Detail Pendaftaran: {enrollment.student.username}',
                           enrollment=enrollment,
                           expected_price=expected_price,
                           paid_price=paid_price)

@app.route('/admin/certificates')
@login_required
@admin_required
def admin_certificates():
    # Ambil semua pendaftaran yang sudah dikonfirmasi (is_confirmed=True)
    # dan yang progres kursusnya sudah 100%
    
    confirmed_enrollments = Enrollment.query.filter_by(is_confirmed=True).all()
    
    certificate_data = []
    for enrollment in confirmed_enrollments:
        course = enrollment.course
        user = enrollment.student
        progress = course.get_progress(user.id)
        
        if progress == 100:
            certificate_data.append({
                'enrollment': enrollment,
                'user': user,
                'course': course,
                'progress': progress
            })
            
    return render_template('admin/certificates.html',
                           title='Manajemen Sertifikat',
                           certificate_data=certificate_data)

@app.route('/admin/certificate_preview/<int:enrollment_id>')
@login_required
@admin_required
def certificate_preview(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    # Pastikan kursus selesai dan terkonfirmasi
    course = enrollment.course
    user = enrollment.student
    
    if not enrollment.is_confirmed or course.get_progress(user.id) != 100:
        flash('Sertifikat belum memenuhi syarat untuk dicetak.', 'danger')
        return redirect(url_for('admin_certificates'))
        
    # Data yang akan dicetak
    certificate_data = {
        'full_name': user.full_name or user.username,
        'course_title': course.title,
        'completion_date': enrollment.timestamp.strftime('%d %B %Y'),
        'certificate_id': f"JK-{enrollment.id}-{enrollment.timestamp.year}"
    }
    
    # Render template khusus tanpa base.html
    return render_template('admin/certificate_preview.html', 
                           data=certificate_data)

@app.route('/certificate/download/<int:enrollment_id>')
@login_required
def user_certificate_download(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    
    # 1. Verifikasi Kepemilikan dan Status
    if enrollment.user_id != current_user.id:
        flash('Akses ditolak. Sertifikat ini bukan milik Anda.', 'danger')
        return redirect(url_for('dashboard'))
        
    course = enrollment.course
    user = enrollment.student
    
    if not enrollment.is_confirmed or course.get_progress(user.id) != 100:
        flash('Sertifikat belum memenuhi syarat untuk diunduh (Kursus belum 100% selesai atau pembayaran belum dikonfirmasi).', 'danger')
        return redirect(url_for('profile'))
        
    # 2. Data Sertifikat
    certificate_data = {
        'full_name': user.full_name or user.username,
        'course_title': course.title,
        'completion_date': enrollment.timestamp.strftime('%d %B %Y'),
        'certificate_id': f"JK-{enrollment.id}-{enrollment.timestamp.year}"
    }
    
    # 3. Render template khusus tanpa base.html
    # Kita akan menggunakan template yang sama dengan admin preview
    return render_template('admin/certificate_preview.html', 
                           data=certificate_data)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    form = AdminUserForm()
    
    if form.validate_on_submit():
        # Cek email unik secara manual (jika Anda ingin memaksanya)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email ini sudah terdaftar. Gunakan email lain.', 'danger')
            return redirect(url_for('admin_add_user'))
            
        user = User(
            username=form.username.data, 
            email=form.email.data,
            is_admin=form.is_admin.data,
            full_name=form.full_name.data,
            whatsapp_number=form.whatsapp_number.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        flash(f'Pengguna "{user.username}" berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_users'))
        
    return render_template('admin/add_user.html', title='Tambah Pengguna Baru', form=form)
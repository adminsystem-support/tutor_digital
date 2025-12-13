from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_ 
from sqlalchemy.ext.hybrid import hybrid_property

# --- MODEL DATABASE ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)

    full_name = db.Column(db.String(120))
    whatsapp_number = db.Column(db.String(20))
    
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    progresses = db.relationship('LessonProgress', backref='student', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(64), default='Umum')
    
    instructor_name = db.Column(db.String(100))
    instructor_title = db.Column(db.String(100))
    rating = db.Column(db.Float, default=0.0)
    price = db.Column(db.Integer, default=0)
    discount_percent = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255), default='https://via.placeholder.com/400x200.png?text=Jago+Komputer')
    instructor_image_url = db.Column(db.String(255), default='https://via.placeholder.com/30')
    
    lessons = db.relationship('Lesson', backref='course', lazy='dynamic')
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')

    def total_lessons(self):
        return self.lessons.count()

    def get_progress(self, user_id):
        total = self.total_lessons()
        if total == 0:
            return 0
        
        completed = LessonProgress.query.join(Lesson).filter(
            Lesson.course_id == self.id,
            LessonProgress.user_id == user_id,
            LessonProgress.is_completed == True
        ).count()
        
        return int((completed / total) * 100)

    @hybrid_property
    def final_price(self):
        return self.price - (self.price * self.discount_percent / 100)

    def __repr__(self):
        return f'<Course {self.title}>'

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    order = db.Column(db.Integer)

    progresses = db.relationship('LessonProgress', backref='lesson', lazy='dynamic')

    def __repr__(self):
        return f'<Lesson {self.title}>'

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    timestamp = db.Column(db.DateTime, index=True, default=db.func.now())
    unique_code = db.Column(db.Integer, default=0)

    payment_method = db.Column(db.String(64))
    proof_of_payment = db.Column(db.String(256))
    
    is_paid = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='_user_course_uc'),)

class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    is_completed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id', name='_user_lesson_uc'),)

# --- LOGIN MANAGER ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
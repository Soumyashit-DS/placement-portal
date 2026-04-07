"""
Database Table Definitions (5 tables)
======================================
User, StudentProfile, CompanyProfile, PlacementDrive, Application
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Login info for all users (admin, company, student)."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)       # 'admin', 'company', 'student'
    is_active = db.Column(db.Boolean, default=True)       # False = blacklisted
    is_approved = db.Column(db.Boolean, default=False)    # Companies need admin approval
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student_profile = db.relationship('StudentProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')
    company_profile = db.relationship('CompanyProfile', back_populates='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudentProfile(db.Model):
    """Extra details for student users."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    cgpa = db.Column(db.Float, nullable=True)
    phone_no = db.Column(db.String(15), nullable=True)
    resume_filename = db.Column(db.String(255), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', back_populates='student_profile')
    applications = db.relationship('Application', back_populates='student_profile', lazy='dynamic', cascade='all, delete-orphan')


class CompanyProfile(db.Model):
    """Extra details for company users."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(15), nullable=True)

    user = db.relationship('User', back_populates='company_profile')
    drives = db.relationship('PlacementDrive', back_populates='company_profile', lazy='dynamic', cascade='all, delete-orphan')


class PlacementDrive(db.Model):
    """A job/recruitment drive created by a company."""
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    salary_package = db.Column(db.String(50), nullable=True)
    eligibility_cgpa = db.Column(db.Float, default=0.0)
    eligible_departments = db.Column(db.String(300), nullable=True)
    drive_date = db.Column(db.Date, nullable=True)
    last_apply_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='Pending')  # Pending / Approved / Closed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    company_profile = db.relationship('CompanyProfile', back_populates='drives')
    applications = db.relationship('Application', back_populates='placement_drive', lazy='dynamic', cascade='all, delete-orphan')


class Application(db.Model):
    """A student's application to a placement drive."""
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    status = db.Column(db.String(20), default='Applied')  # Applied / Shortlisted / Selected / Rejected
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))

    student_profile = db.relationship('StudentProfile', back_populates='applications')
    placement_drive = db.relationship('PlacementDrive', back_populates='applications')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),
    )

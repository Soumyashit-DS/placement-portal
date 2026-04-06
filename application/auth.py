"""Login, Register, Logout routes"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import db, User, StudentProfile, CompanyProfile

auth_bp = Blueprint('auth', __name__)


# ─── FORMS ───────────────────────────────────────────────────────────

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class StudentRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired()])
    roll_number = StringField('Roll Number', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    cgpa = FloatField('CGPA', validators=[Optional(), NumberRange(min=0, max=10)])
    phone_no = StringField('Phone_No', validators=[Optional()])
    graduation_year = IntegerField('Graduation Year', validators=[Optional()])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class CompanyRegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    company_name = StringField('Company Name', validators=[DataRequired()])
    industry = StringField('Industry', validators=[Optional()])
    website = StringField('Website', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    contact_person = StringField('Contact Person', validators=[Optional()])
    contact_phone = StringField('Contact Phone', validators=[Optional()])
    submit = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


# ─── ROUTES ──────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role()
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        if not user.is_active:
            flash('Account deactivated. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))
        if user.role == 'company' and not user.is_approved:
            flash('Pending admin approval.', 'warning')
            return redirect(url_for('auth.login'))
        login_user(user)
        flash(f'Welcome, {user.username}!', 'success')
        return _redirect_by_role()
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role()
    # Student registration by default
    form = StudentRegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                     role='student', is_approved=True, is_active=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        db.session.add(StudentProfile(
            user_id=user.id, full_name=form.full_name.data,
            roll_number=form.roll_number.data, department=form.department.data,
            cgpa=form.cgpa.data, phone_no=form.phone_no.data,
            graduation_year=form.graduation_year.data))
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, type='student')


@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return _redirect_by_role()
    form = CompanyRegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data,
                     role='company', is_approved=False, is_active=True)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()
        db.session.add(CompanyProfile(
            user_id=user.id, company_name=form.company_name.data,
            industry=form.industry.data, website=form.website.data,
            description=form.description.data, contact_person=form.contact_person.data,
            contact_phone=form.contact_phone.data))
        db.session.commit()
        flash('Registered! Awaiting admin approval.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, type='company')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role():
    if current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'company':
        return redirect(url_for('company.dashboard'))
    return redirect(url_for('student.dashboard'))

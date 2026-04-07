"""All student routes"""

import os
import time
from datetime import date
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from werkzeug.utils import secure_filename
from models import db, PlacementDrive, Application

student_bp = Blueprint('student', __name__)


def student_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role != 'student':
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ─── FORMS ───────────────────────────────────────────────────────────

class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    cgpa = FloatField('CGPA', validators=[Optional(), NumberRange(min=0, max=10)])
    phone = StringField('Phone', validators=[Optional()])
    graduation_year = IntegerField('Graduation Year', validators=[Optional()])
    submit = SubmitField('Update Profile')


class ResumeForm(FlaskForm):
    resume = FileField('Resume (PDF only)', validators=[DataRequired(), FileAllowed(['pdf'], 'PDF only.')])
    submit = SubmitField('Upload')


# ─── ROUTES ──────────────────────────────────────────────────────────

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    p = current_user.student_profile
    return render_template('student/dashboard.html', profile=p,
        total=p.applications.count(),
        selected=p.applications.filter_by(status='Selected').count(),
        pending=p.applications.filter_by(status='Applied').count(),
        rejected=p.applications.filter_by(status='Rejected').count(),
        drives=PlacementDrive.query.filter_by(status='Approved').order_by(PlacementDrive.created_at.desc()).limit(5).all(),
        recent_apps=p.applications.order_by(Application.applied_at.desc()).limit(5).all())


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    sp = current_user.student_profile
    form = ProfileForm(obj=sp)
    resume_form = ResumeForm()
    if form.validate_on_submit():
        sp.full_name = form.full_name.data
        sp.department = form.department.data
        sp.cgpa = form.cgpa.data
        sp.phone_no = form.phone.data
        sp.graduation_year = form.graduation_year.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('student.profile'))
    return render_template('student/profile.html', form=form, resume_form=resume_form, sp=sp)


@student_bp.route('/upload-resume', methods=['POST'])
@login_required
@student_required
def upload_resume():
    resume_form = ResumeForm()
    if resume_form.validate_on_submit():
        file = resume_form.resume.data
        sp = current_user.student_profile
        filename = secure_filename(f"{sp.id}_{int(time.time())}.pdf")
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        old_filename = sp.resume_filename
        try:
            file.save(filepath)
        except OSError:
            flash('Failed to save resume. Please try again.', 'danger')
            return redirect(url_for('student.profile'))
        sp.resume_filename = filename
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            os.remove(filepath)
            flash('Failed to update profile. Please try again.', 'danger')
            return redirect(url_for('student.profile'))
        if old_filename:
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        flash('Resume uploaded.', 'success')
    else:
        flash('Only PDF files allowed.', 'danger')
    return redirect(url_for('student.profile'))


@student_bp.route('/drives')
@login_required
@student_required
def browse_drives():
    q = request.args.get('q', '')
    query = PlacementDrive.query.filter_by(status='Approved')
    if q:
        query = query.filter((PlacementDrive.title.ilike(f'%{q}%')) | (PlacementDrive.location.ilike(f'%{q}%')))
    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    applied = {a.drive_id for a in Application.query.filter_by(student_id=current_user.student_profile.id).all()}
    return render_template('student/dashboard.html', browse=True, drives=drives, q=q, applied=applied, profile=current_user.student_profile)


@student_bp.route('/drives/<int:id>')
@login_required
@student_required
def view_drive(id):
    drive = db.get_or_404(PlacementDrive, id)
    if drive.status != 'Approved':
        abort(404)
    already = Application.query.filter_by(student_id=current_user.student_profile.id, drive_id=id).first() is not None
    return render_template('student/dashboard.html', view_drive=drive, already_applied=already, profile=current_user.student_profile)


@student_bp.route('/drives/<int:id>/apply', methods=['POST'])
@login_required
@student_required
def apply_drive(id):
    drive = db.get_or_404(PlacementDrive, id)
    sp = current_user.student_profile

    if drive.status != 'Approved':
        flash('Not accepting applications.', 'danger')
        return redirect(url_for('student.browse_drives'))

    if Application.query.filter_by(student_id=sp.id, drive_id=id).first():
        flash('Already applied.', 'warning')
        return redirect(url_for('student.browse_drives'))

    # Deadline check
    if drive.last_apply_date and date.today() > drive.last_apply_date:
        flash('Application deadline has passed.', 'danger')
        return redirect(url_for('student.browse_drives'))

    # CGPA eligibility check
    student_cgpa = sp.cgpa or 0.0
    if student_cgpa < (drive.eligibility_cgpa or 0.0):
        flash(f'You need a minimum CGPA of {drive.eligibility_cgpa} to apply.', 'danger')
        return redirect(url_for('student.browse_drives'))

    # Department eligibility check
    if drive.eligible_departments:
        allowed = [d.strip().lower() for d in drive.eligible_departments.split(',')]
        if sp.department.strip().lower() not in allowed:
            flash('Your department is not eligible for this drive.', 'danger')
            return redirect(url_for('student.browse_drives'))

    db.session.add(Application(student_id=sp.id, drive_id=id, status='Applied'))
    db.session.commit()
    flash('Application submitted!', 'success')
    return redirect(url_for('student.my_applications'))


@student_bp.route('/applications')
@login_required
@student_required
def my_applications():
    apps = current_user.student_profile.applications.order_by(Application.applied_at.desc()).all()
    return render_template('student/dashboard.html', my_apps=apps, profile=current_user.student_profile)


@student_bp.route('/history')
@login_required
@student_required
def history():
    placed = current_user.student_profile.applications.filter_by(status='Selected').all()
    return render_template('student/history.html', placements=placed)

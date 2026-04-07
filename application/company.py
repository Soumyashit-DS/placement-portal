"""All company routes"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange
from models import db, PlacementDrive, Application

company_bp = Blueprint('company', __name__)


def company_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role != 'company':
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ─── FORMS ───────────────────────────────────────────────────────────

class DriveForm(FlaskForm):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    salary_package = StringField('Salary Package', validators=[Optional()])
    eligibility_cgpa = FloatField('Minimum CGPA', validators=[Optional(), NumberRange(min=0, max=10)], default=0.0)
    eligible_departments = StringField('Eligible Departments', validators=[Optional()])
    drive_date = DateField('Drive Date', validators=[Optional()], format='%Y-%m-%d')
    last_apply_date = DateField('Application Deadline', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Save')


class ProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    industry = StringField('Industry', validators=[Optional()])
    website = StringField('Website', validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional()])
    contact_person = StringField('Contact Person', validators=[Optional()])
    contact_phone = StringField('Contact Phone', validators=[Optional()])
    submit = SubmitField('Update Profile')


# ─── ROUTES ──────────────────────────────────────────────────────────

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    if not current_user.is_approved:
        return render_template('company/dashboard.html', approved=False)
    profile = current_user.company_profile
    total_drives = profile.drives.count()
    total_apps = Application.query.join(PlacementDrive).filter(PlacementDrive.company_id == profile.id).count()
    selected = Application.query.join(PlacementDrive).filter(PlacementDrive.company_id == profile.id, Application.status == 'Selected').count()
    drives = profile.drives.order_by(PlacementDrive.created_at.desc()).limit(5).all()
    return render_template('company/dashboard.html', approved=True, profile=profile,
                           total_drives=total_drives, total_apps=total_apps,
                           selected=selected, drives=drives)


@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@company_required
def profile():
    cp = current_user.company_profile
    form = ProfileForm(obj=cp)
    if form.validate_on_submit():
        cp.company_name = form.company_name.data
        cp.industry = form.industry.data
        cp.website = form.website.data
        cp.description = form.description.data
        cp.contact_person = form.contact_person.data
        cp.contact_phone = form.contact_phone.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('company.profile'))
    return render_template('company/dashboard.html', approved=current_user.is_approved,
                           profile=cp, form=form, show_profile=True)


@company_bp.route('/drives')
@login_required
@company_required
def my_drives():
    if not current_user.is_approved:
        flash('Pending approval.', 'warning')
        return redirect(url_for('company.dashboard'))
    drives = current_user.company_profile.drives.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('company/dashboard.html', approved=True, drives=drives,
                           profile=current_user.company_profile, show_drives=True)


@company_bp.route('/drives/create', methods=['GET', 'POST'])
@login_required
@company_required
def create_drive():
    if not current_user.is_approved:
        flash('Pending approval.', 'warning')
        return redirect(url_for('company.dashboard'))
    form = DriveForm()
    if form.validate_on_submit():
        drive = PlacementDrive(company_id=current_user.company_profile.id,
            title=form.title.data, description=form.description.data,
            location=form.location.data, salary_package=form.salary_package.data,
            eligibility_cgpa=form.eligibility_cgpa.data or 0.0,
            eligible_departments=form.eligible_departments.data,
            drive_date=form.drive_date.data, last_apply_date=form.last_apply_date.data,
            status='Pending')
        db.session.add(drive)
        db.session.commit()
        flash('Drive created! Awaiting approval.', 'success')
        return redirect(url_for('company.my_drives'))
    return render_template('company/create_drive.html', form=form)


@company_bp.route('/drives/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(id):
    drive = db.get_or_404(PlacementDrive, id)
    if drive.company_id != current_user.company_profile.id:
        abort(403)
    form = DriveForm(obj=drive)
    if form.validate_on_submit():
        drive.title = form.title.data
        drive.description = form.description.data
        drive.location = form.location.data
        drive.salary_package = form.salary_package.data
        drive.eligibility_cgpa = form.eligibility_cgpa.data or 0.0
        drive.eligible_departments = form.eligible_departments.data
        drive.drive_date = form.drive_date.data
        drive.last_apply_date = form.last_apply_date.data
        drive.status = 'Pending'  # reset to re-trigger admin approval after edits
        db.session.commit()
        flash('Drive updated. Awaiting re-approval.', 'success')
        return redirect(url_for('company.my_drives'))
    return render_template('company/edit_drive.html', form=form, drive=drive)


@company_bp.route('/drives/<int:id>/close', methods=['POST'])
@login_required
@company_required
def close_drive(id):
    drive = db.get_or_404(PlacementDrive, id)
    if drive.company_id != current_user.company_profile.id:
        abort(403)
    drive.status = 'Closed'
    db.session.commit()
    flash('Drive closed.', 'info')
    return redirect(url_for('company.my_drives'))


@company_bp.route('/drives/<int:id>/delete', methods=['POST'])
@login_required
@company_required
def delete_drive(id):
    drive = db.get_or_404(PlacementDrive, id)
    if drive.company_id != current_user.company_profile.id:
        abort(403)
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'info')
    return redirect(url_for('company.my_drives'))


@company_bp.route('/drives/<int:id>/applications')
@login_required
@company_required
def applications(id):
    drive = db.get_or_404(PlacementDrive, id)
    if drive.company_id != current_user.company_profile.id:
        abort(403)
    return render_template('company/applications.html', drive=drive, apps=drive.applications.all())


@company_bp.route('/applications/<int:id>/update/<status>', methods=['POST'])
@login_required
@company_required
def update_application(id, status):
    if status not in ('Shortlisted', 'Selected', 'Rejected'):
        abort(400)
    application = db.get_or_404(Application, id)
    drive = db.get_or_404(PlacementDrive, application.drive_id)
    if drive.company_id != current_user.company_profile.id:
        abort(403)
    application.status = status
    db.session.commit()
    flash(f'Status → {status}.', 'success')
    return redirect(url_for('company.applications', id=drive.id))

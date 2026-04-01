"""All admin routes"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ─── DASHBOARD ───────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_students': StudentProfile.query.count(),
        'total_companies': CompanyProfile.query.count(),
        'pending_companies': User.query.filter_by(role='company', is_approved=False, is_active=True).count(),
        'total_drives': PlacementDrive.query.count(),
        'pending_drives': PlacementDrive.query.filter_by(status='Pending').count(),
        'total_applications': Application.query.count(),
        'selected_students': Application.query.filter_by(status='Selected').count(),
    }
    return render_template('admin/dashboard.html', stats=stats)


# ─── COMPANIES (approve/reject/manage) ──────────────────────────────

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    tab = request.args.get('tab', 'all')   # 'all' or 'pending'
    query = request.args.get('q', '')
    if tab == 'pending':
        items = User.query.filter_by(role='company', is_approved=False, is_active=True).all()
    elif query:
        items = CompanyProfile.query.filter(CompanyProfile.company_name.ilike(f'%{query}%')).all()
    else:
        items = CompanyProfile.query.all()
    return render_template('admin/companies.html', items=items, tab=tab, query=query)


@admin_bp.route('/approve-company/<int:id>', methods=['POST'])
@login_required
@admin_required
def approve_company(id):
    user = User.query.get_or_404(id)
    user.is_approved = True
    db.session.commit()
    flash(f'"{user.company_profile.company_name}" approved.', 'success')
    return redirect(url_for('admin.companies', tab='pending'))


@admin_bp.route('/reject-company/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_company(id):
    user = User.query.get_or_404(id)
    name = user.company_profile.company_name
    db.session.delete(user)
    db.session.commit()
    flash(f'"{name}" rejected.', 'info')
    return redirect(url_for('admin.companies', tab='pending'))


# ─── STUDENTS (search/blacklist) ─────────────────────────────────────

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    query = request.args.get('q', '')
    if query:
        items = StudentProfile.query.filter(
            (StudentProfile.full_name.ilike(f'%{query}%')) |
            (StudentProfile.roll_number.ilike(f'%{query}%')) |
            (StudentProfile.phone.ilike(f'%{query}%'))).all()
    else:
        items = StudentProfile.query.all()
    return render_template('admin/students.html', items=items, query=query)


# ─── BLACKLIST (toggle active) ──────────────────────────────────────

@admin_bp.route('/blacklist/<int:id>', methods=['POST'])
@login_required
@admin_required
def blacklist_user(id):
    user = User.query.get_or_404(id)
    if user.role == 'admin':
        flash('Cannot blacklist admin.', 'danger')
        return redirect(url_for('admin.dashboard'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'"{user.username}" {"activated" if user.is_active else "deactivated"}.', 'info')
    if user.role == 'student':
        return redirect(url_for('admin.students'))
    return redirect(url_for('admin.companies'))


# ─── DRIVES (all + approve/reject pending) ──────────────────────────

@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    tab = request.args.get('tab', 'all')
    if tab == 'pending':
        items = PlacementDrive.query.filter_by(status='Pending').all()
    else:
        items = PlacementDrive.query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin/drives.html', items=items, tab=tab)


@admin_bp.route('/approve-drive/<int:id>', methods=['POST'])
@login_required
@admin_required
def approve_drive(id):
    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'Approved'
    db.session.commit()
    flash(f'"{drive.title}" approved.', 'success')
    return redirect(url_for('admin.drives', tab='pending'))


@admin_bp.route('/reject-drive/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_drive(id):
    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'Closed'
    db.session.commit()
    flash(f'"{drive.title}" rejected.', 'info')
    return redirect(url_for('admin.drives', tab='pending'))


# ─── APPLICATIONS (view all) ────────────────────────────────────────

@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    items = Application.query.order_by(Application.applied_at.desc()).all()
    return render_template('admin/applications.html', items=items)

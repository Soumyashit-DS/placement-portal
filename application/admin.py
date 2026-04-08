"""All admin routes"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from models import db, User, StudentProfile, CompanyProfile, PlacementDrive, Application

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapped


# ─── DASHBOARD ───────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from sqlalchemy import func
    stats = {
        'total_students': StudentProfile.query.count(),
        'total_companies': CompanyProfile.query.count(),
        'pending_companies': User.query.filter_by(role='company', is_approved=False, is_active=True).count(),
        'total_drives': PlacementDrive.query.count(),
        'pending_drives': PlacementDrive.query.filter_by(status='Pending').count(),
        'total_applications': Application.query.count(),
        'selected_students': Application.query.filter_by(status='Selected').count(),
    }

    # Applications per company for bar chart
    rows = (
        db.session.query(CompanyProfile.company_name, func.count(Application.id).label('cnt'))
        .join(PlacementDrive, PlacementDrive.company_id == CompanyProfile.id)
        .join(Application, Application.drive_id == PlacementDrive.id)
        .group_by(CompanyProfile.company_name)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    apps_per_company = [{'name': r.company_name, 'count': r.cnt} for r in rows]
    max_apps = apps_per_company[0]['count'] if apps_per_company else 1

    total_apps = stats['total_applications'] or 1  # avoid division by zero
    placement_rate  = round(Application.query.filter_by(status='Selected').count()   / total_apps * 100, 1)
    shortlist_rate  = round(Application.query.filter_by(status='Shortlisted').count() / total_apps * 100, 1)
    rejection_rate  = round(Application.query.filter_by(status='Rejected').count()   / total_apps * 100, 1)

    return render_template('admin/dashboard.html', stats=stats,
        apps_per_company=apps_per_company, max_apps=max_apps,
        placement_rate=placement_rate,
        shortlist_rate=shortlist_rate,
        rejection_rate=rejection_rate)


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
    user = db.get_or_404(User, id)
    user.is_approved = True
    db.session.commit()
    name = user.company_profile.company_name if user.company_profile else user.username
    flash(f'"{name}" approved.', 'success')
    return redirect(url_for('admin.companies', tab='pending'))


@admin_bp.route('/reject-company/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_company(id):
    user = db.get_or_404(User, id)
    name = user.company_profile.company_name if user.company_profile else user.username
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
            (StudentProfile.phone_no.ilike(f'%{query}%'))).all()
    else:
        items = StudentProfile.query.all()
    return render_template('admin/students.html', items=items, query=query)


# ─── BLACKLIST (toggle active) ──────────────────────────────────────

@admin_bp.route('/blacklist/<int:id>', methods=['POST'])
@login_required
@admin_required
def blacklist_user(id):
    user = db.get_or_404(User, id)
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
    drive = db.get_or_404(PlacementDrive, id)
    drive.status = 'Approved'
    db.session.commit()
    flash(f'"{drive.title}" approved.', 'success')
    return redirect(url_for('admin.drives', tab='pending'))


@admin_bp.route('/reject-drive/<int:id>', methods=['POST'])
@login_required
@admin_required
def reject_drive(id):
    drive = db.get_or_404(PlacementDrive, id)
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


# ─── STATS ──────────────────────────────────────────────────────────

@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    total_students = StudentProfile.query.count()

    placed_ids = db.session.query(Application.student_id).filter_by(status='Selected').distinct().all()
    total_placed = len(placed_ids)
    placement_pct = round((total_placed / total_students * 100), 1) if total_students else 0

    # Top 5 companies by selection count
    from sqlalchemy import func
    top_companies_raw = (
        db.session.query(CompanyProfile.company_name, func.count(Application.id).label('cnt'))
        .join(PlacementDrive, PlacementDrive.company_id == CompanyProfile.id)
        .join(Application, Application.drive_id == PlacementDrive.id)
        .filter(Application.status == 'Selected')
        .group_by(CompanyProfile.company_name)
        .order_by(func.count(Application.id).desc())
        .limit(5)
        .all()
    )
    top_companies = [{'name': r[0], 'count': r[1]} for r in top_companies_raw]
    max_company_count = top_companies[0]['count'] if top_companies else 1

    # Department-wise placement count
    dept_raw = (
        db.session.query(StudentProfile.department, func.count(Application.id).label('cnt'))
        .join(Application, Application.student_id == StudentProfile.id)
        .filter(Application.status == 'Selected')
        .group_by(StudentProfile.department)
        .order_by(func.count(Application.id).desc())
        .all()
    )
    dept_stats = [{'dept': r[0], 'count': r[1]} for r in dept_raw]
    max_dept_count = dept_stats[0]['count'] if dept_stats else 1

    return render_template('admin/stats.html',
        total_students=total_students,
        total_placed=total_placed,
        placement_pct=placement_pct,
        top_companies=top_companies,
        max_company_count=max_company_count,
        dept_stats=dept_stats,
        max_dept_count=max_dept_count,
    )


# ─── SUMMARY ────────────────────────────────────────────────────────

@admin_bp.route('/summary')
@login_required
@admin_required
def summary():
    from sqlalchemy import func

    # All approved companies with aggregated counts in one query
    rows = (
        db.session.query(
            CompanyProfile.company_name,
            func.count(PlacementDrive.id.distinct()).label('total_drives'),
            func.count(Application.id).label('total_applicants'),
            func.sum(db.case((Application.status == 'Selected', 1), else_=0)).label('total_selected'),
        )
        .join(PlacementDrive, PlacementDrive.company_id == CompanyProfile.id, isouter=True)
        .join(Application, Application.drive_id == PlacementDrive.id, isouter=True)
        .join(User, User.id == CompanyProfile.user_id)
        .filter(User.is_approved == True)
        .group_by(CompanyProfile.id, CompanyProfile.company_name)
        .order_by(func.sum(db.case((Application.status == 'Selected', 1), else_=0)).desc())
        .all()
    )

    companies = [
        {
            'name': r.company_name,
            'drives': r.total_drives or 0,
            'applicants': r.total_applicants or 0,
            'selected': int(r.total_selected or 0),
        }
        for r in rows
    ]

    max_applicants = max((c['applicants'] for c in companies), default=1) or 1
    max_selected  = max((c['selected']   for c in companies), default=1) or 1

    return render_template('admin/summary.html',
        companies=companies,
        max_applicants=max_applicants,
        max_selected=max_selected,
    )

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime

company_bp = Blueprint('company', __name__)

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'company':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        if not current_user.company_profile.approved:
            flash('Your account is not approved yet.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    from models import Drive
    db = current_app.db
    company = current_user.company_profile
    drives = company.drives.all()
    drive_counts = []
    for drive in drives:
        count = drive.applications.count()
        drive_counts.append((drive, count))
    return render_template('company/dashboard.html', company=company, drive_counts=drive_counts)

@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@company_required
def profile():
    company = current_user.company_profile
    db = current_app.db
    if request.method == 'POST':
        company.company_name = request.form.get('company_name')
        company.hr_contact = request.form.get('hr_contact')
        company.website = request.form.get('website')
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('company.dashboard'))
    return render_template('company/profile.html', company=company)

@company_bp.route('/drives')
@login_required
@company_required
def drives():
    company = current_user.company_profile
    drives = company.drives.all()
    return render_template('company/drives.html', drives=drives)

@company_bp.route('/drives/create', methods=['GET', 'POST'])
@login_required
@company_required
def create_drive():
    from models import Drive
    db = current_app.db
    if request.method == 'POST':
        job_title = request.form.get('job_title')
        description = request.form.get('description')
        eligibility = request.form.get('eligibility')
        deadline_str = request.form.get('deadline')
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        drive = Drive(
            company_id=current_user.id,
            job_title=job_title,
            description=description,
            eligibility=eligibility,
            deadline=deadline,
            status='pending'
        )
        db.session.add(drive)
        db.session.commit()
        flash('Placement drive created, pending admin approval.', 'success')
        return redirect(url_for('company.drives'))
    return render_template('company/create_drive.html')

@company_bp.route('/drives/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(id):
    from models import Drive
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.drives'))
    if request.method == 'POST':
        drive.job_title = request.form.get('job_title')
        drive.description = request.form.get('description')
        drive.eligibility = request.form.get('eligibility')
        deadline_str = request.form.get('deadline')
        drive.deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        db.session.commit()
        flash('Drive updated.', 'success')
        return redirect(url_for('company.drives'))
    return render_template('company/edit_drive.html', drive=drive)

@company_bp.route('/drives/<int:id>/delete', methods=['POST'])
@login_required
@company_required
def delete_drive(id):
    from models import Drive
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.drives'))
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'success')
    return redirect(url_for('company.drives'))

@company_bp.route('/drives/<int:id>/close', methods=['POST'])
@login_required
@company_required
def close_drive(id):
    from models import Drive
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.drives'))
    drive.status = 'closed'
    db.session.commit()
    flash('Drive closed.', 'success')
    return redirect(url_for('company.drives'))

@company_bp.route('/drives/<int:id>/applications')
@login_required
@company_required
def view_applications(id):
    from models import Drive, Application
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.drives'))
    applications = drive.applications.all()
    return render_template('company/applications.html', drive=drive, applications=applications)

@company_bp.route('/applications/<int:id>/update', methods=['POST'])
@login_required
@company_required
def update_application_status(id):
    from models import Application
    db = current_app.db
    application = db.session.query(Application).get_or_404(id)
    drive = application.drive
    if drive.company_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('company.drives'))
    status = request.form.get('status')
    if status in ['applied', 'shortlisted', 'selected', 'rejected']:
        application.status = status
        db.session.commit()
        flash('Application status updated.', 'success')
    return redirect(url_for('company.view_applications', id=drive.id))

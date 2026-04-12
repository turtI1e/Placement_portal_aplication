from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
import os
from werkzeug.utils import secure_filename

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx'}

# ---------- Eligibility Helpers ----------
def parse_eligibility(eligibility_str):
    """Parse eligibility string like 'branch:CS,IT; min_cgpa:7.0; year:3,4'"""
    criteria = {}
    if not eligibility_str:
        return criteria
    parts = [p.strip() for p in eligibility_str.split(';') if p.strip()]
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            if key == 'branch':
                criteria['branches'] = [b.strip().lower() for b in value.split(',')]
            elif key == 'min_cgpa':
                try:
                    criteria['min_cgpa'] = float(value)
                except ValueError:
                    pass
            elif key == 'year':
                criteria['years'] = [int(y.strip()) for y in value.split(',') if y.strip().isdigit()]
    return criteria

def is_student_eligible(student, criteria):
    """Return (is_eligible, reason_message)"""
    if not criteria:
        return True, ""
    if 'branches' in criteria and student.branch:
        if student.branch.lower() not in criteria['branches']:
            return False, f"Branch {student.branch} not allowed. Allowed: {', '.join(criteria['branches'])}"
    if 'min_cgpa' in criteria and student.cgpa is not None:
        if student.cgpa < criteria['min_cgpa']:
            return False, f"CGPA {student.cgpa} is below minimum {criteria['min_cgpa']}"
    if 'years' in criteria and student.year is not None:
        if student.year not in criteria['years']:
            return False, f"Year {student.year} not allowed. Allowed years: {criteria['years']}"
    return True, ""

# ---------- Routes ----------
@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    from models import Drive, Application
    db = current_app.db
    student = current_user.student_profile
    drives = db.session.query(Drive).filter_by(status='approved').all()
    applied_drives = [app.drive for app in student.applications]
    return render_template('student/dashboard.html', student=student, drives=drives, applied_drives=applied_drives)

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    student = current_user.student_profile
    db = current_app.db
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.contact = request.form.get('contact')
        student.branch = request.form.get('branch')
        year_str = request.form.get('year')
        student.year = int(year_str) if year_str else None
        cgpa_str = request.form.get('cgpa')
        student.cgpa = float(cgpa_str) if cgpa_str else None
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"student_{current_user.id}_{file.filename}")
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file.save(os.path.join(upload_folder, filename))
                student.resume_path = filename
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('student.dashboard'))
    return render_template('student/profile.html', student=student)

@student_bp.route('/drives')
@login_required
@student_required
def drives():
    from models import Drive
    db = current_app.db
    drives = db.session.query(Drive).filter_by(status='approved').all()
    applied_ids = [app.drive_id for app in current_user.student_profile.applications]
    return render_template('student/drives.html', drives=drives, applied_ids=applied_ids)

@student_bp.route('/drives/<int:id>/apply', methods=['POST'])
@login_required
@student_required
def apply_drive(id):
    from models import Drive, Application
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    if drive.status != 'approved':
        flash('This drive is not open for applications.', 'warning')
        return redirect(url_for('student.drives'))

    student = current_user.student_profile

    # Eligibility check
    criteria = parse_eligibility(drive.eligibility)
    eligible, reason = is_student_eligible(student, criteria)
    if not eligible:
        flash(f'You are not eligible for this drive: {reason}', 'danger')
        return redirect(url_for('student.drives'))

    existing = db.session.query(Application).filter_by(student_id=student.user_id, drive_id=id).first()
    if existing:
        flash('You have already applied for this drive.', 'warning')
    else:
        application = Application(student_id=student.user_id, drive_id=id, status='applied')
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully.', 'success')
    return redirect(url_for('student.drives'))

@student_bp.route('/applications')
@login_required
@student_required
def applications():
    student = current_user.student_profile
    applications = student.applications.all()
    return render_template('student/applications.html', applications=applications)

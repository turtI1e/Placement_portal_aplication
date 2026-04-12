from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from models import Student, Company, Drive, Application
    db = current_app.db
    total_students = db.session.query(Student).count()
    total_companies = db.session.query(Company).count()
    total_drives = db.session.query(Drive).count()
    total_applications = db.session.query(Application).count()
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_companies=total_companies,
                           total_drives=total_drives,
                           total_applications=total_applications)

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    from models import Student, User
    db = current_app.db
    search = request.args.get('search', '')
    query = db.session.query(Student).join(User)
    if search:
        # Try to search by ID if search is numeric
        if search.isdigit():
            query = query.filter(Student.user_id == int(search))
        else:
            query = query.filter(
                (Student.name.contains(search)) |
                (Student.contact.contains(search)) |
                (User.email.contains(search))
            )
    students = query.all()
    return render_template('admin/students.html', students=students, search=search)

@admin_bp.route('/students/<int:id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_student(id):
    from models import Student
    db = current_app.db
    student = db.session.query(Student).get_or_404(id)
    user = student.user
    user.is_active = False
    db.session.commit()
    flash(f'Student {student.name} has been blacklisted.', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    from models import Company, User
    db = current_app.db
    search = request.args.get('search', '')
    query = db.session.query(Company).join(User)
    if search:
        query = query.filter(Company.company_name.contains(search))
    companies = query.all()
    return render_template('admin/companies.html', companies=companies, search=search)

@admin_bp.route('/companies/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_company(id):
    from models import Company
    db = current_app.db
    company = db.session.query(Company).get_or_404(id)
    company.approved = True
    db.session.commit()
    flash(f'Company {company.company_name} approved.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/companies/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_company(id):
    from models import Company
    db = current_app.db
    company = db.session.query(Company).get_or_404(id)
    user = company.user
    db.session.delete(company)
    db.session.delete(user)
    db.session.commit()
    flash(f'Company rejected and removed.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/companies/<int:id>/blacklist', methods=['POST'])
@login_required
@admin_required
def blacklist_company(id):
    from models import Company
    db = current_app.db
    company = db.session.query(Company).get_or_404(id)
    user = company.user
    user.is_active = False
    db.session.commit()
    flash(f'Company {company.company_name} blacklisted.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    from models import Drive
    db = current_app.db
    drives = db.session.query(Drive).all()
    return render_template('admin/drives.html', drives=drives)

@admin_bp.route('/drives/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_drive(id):
    from models import Drive
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    drive.status = 'approved'
    db.session.commit()
    flash('Drive approved.', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/drives/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_drive(id):
    from models import Drive
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    drive.status = 'rejected'
    db.session.commit()
    flash('Drive rejected.', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/drives/<int:id>/close', methods=['POST'])
@login_required
@admin_required
def close_drive(id):
    from models import Drive
    db = current_app.db
    drive = db.session.query(Drive).get_or_404(id)
    drive.status = 'closed'
    db.session.commit()
    flash('Drive closed.', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/applications')
@login_required
@admin_required
def all_applications():
    from models import Application
    db = current_app.db
    applications = db.session.query(Application).order_by(Application.application_date.desc()).all()
    return render_template('admin/applications.html', applications=applications)

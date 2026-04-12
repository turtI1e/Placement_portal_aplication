from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    from models import User, Company
    db = current_app.db
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = db.session.query(User).filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            if user.role == 'company' and not user.company_profile.approved:
                flash('Your company account is pending approval.', 'warning')
                return redirect(url_for('auth.login'))
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'company':
                return redirect(url_for('company.dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password or account inactive', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    from models import User, Student
    db = current_app.db
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        contact = request.form.get('contact')
        branch = request.form.get('branch')
        year = request.form.get('year')
        cgpa = request.form.get('cgpa')
        if db.session.query(User).filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register_student'))
        user = User(email=email, role='student', is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        student = Student(
            user_id=user.id,
            name=name,
            contact=contact,
            branch=branch,
            year=int(year) if year else None,
            cgpa=float(cgpa) if cgpa else None
        )
        db.session.add(student)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_student.html')

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    from models import User, Company
    db = current_app.db
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        hr_contact = request.form.get('hr_contact')
        website = request.form.get('website')
        if db.session.query(User).filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register_company'))
        user = User(email=email, role='company', is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        company = Company(user_id=user.id, company_name=company_name, hr_contact=hr_contact, website=website, approved=False)
        db.session.add(company)
        db.session.commit()
        flash('Registration successful! Waiting for admin approval.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register_company.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

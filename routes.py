from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Student, Company ,Placement, Application
from datetime import datetime
from app import app
from sqlalchemy import or_, cast
from sqlalchemy.types import String


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        hashed_password = generate_password_hash(password)

        user = User(
            email=email,
            password=hashed_password,
            user_type=role
        )
        db.session.add(user)
        db.session.commit()

        if role == 'student':
            student = Student(
                user_id=user.id,
                studentname=name,
                institution=request.form['institution'],
                course=request.form['course'],
                year_of_study=request.form['year_of_study'],
                resume_link=request.form['resume_link'],
                cgpa=request.form['cgpa'] if request.form['cgpa'] else None
            )
            db.session.add(student)

        elif role == 'company':
            company = Company(
                user_id=user.id,
                companyname=request.form['companyname'],
                hr_name=request.form['hr_name'],
                hr_contact=request.form['hr_contact']
            )
            db.session.add(company)

        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('User does not exist', 'danger')
            return redirect(url_for('login'))

        if not check_password_hash(user.password, password):
            flash('Incorrect password', 'danger')
            return redirect(url_for('login'))

        if user.user_type != 'admin':
            if user.approval_status == 'pending':
                flash('Admin approval pending', 'warning')
                return redirect(url_for('login'))
            if user.approval_status == 'rejected':
                flash('Admin approval rejected', 'danger')
                return redirect(url_for('login'))

        flash('Login successful', 'success')

        session['user_id'] = user.id
        session['user_type'] = user.user_type
        session['email'] = user.email
        session['role'] = user.user_type

        if user.user_type == 'student':
            return redirect(url_for('student_dash'))
        elif user.user_type == 'company':
            return redirect(url_for('company_dashboard'))
        else:
            return redirect(url_for('admin'))

    return render_template('login.html')



@app.route('/admin')
def admin():
    count_students = User.query.filter_by(user_type='student', approval_status='approved').count()
    count_companies = User.query.filter_by(user_type='company', approval_status='approved').count()
    count_drives = Placement.query.count()
    count_applications = Application.query.count()

    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    return render_template('/admin/admin.html',count_students=count_students, count_companies=count_companies, count_drives=count_drives, count_applications=count_applications)

@app.route('/admin/approval')
def admin_approval():
    pending_users = User.query.filter(User.approval_status == 'pending',User.user_type != 'admin').all()
    return render_template('/admin/approvals.html', users=pending_users)

@app.route('/approve/<int:user_id>')
def approve(user_id):
    user = User.query.get(user_id)
    user.approval_status = 'approved'
    db.session.commit()
    flash('User approved successfully', 'success')
    return redirect(url_for('admin_approval'))

@app.route('/reject/<int:user_id>')
def reject(user_id):
    user = User.query.get(user_id)
    user.approval_status = 'rejected'
    db.session.commit()
    flash('User rejected', 'danger')
    return redirect(url_for('admin_approval'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))



@app.route('/admin/companies')
def admin_companies():
    companies = (
        Company.query
        .join(User, Company.user_id == User.id)
        .filter(User.user_type == 'company', User.approval_status == 'approved')
        .all()
    )
    return render_template('admin/company.html', companies=companies)

@app.route('/admin/students')
def admin_students():
    students = (
        Student.query
        .join(User, Student.user_id == User.id)
        .filter(User.user_type == 'student', User.approval_status == 'approved')
        .all()
    )
    return render_template('admin/student.html', students=students)

@app.route('/admin/company/deactivate/<int:id>')
def deactivate_company(id):
    user = User.query.get_or_404(id)   
    user.is_blacklisted = True         
    db.session.commit()
    flash("Company blacklisted", "success")
    return redirect(url_for('admin_companies'))


@app.route('/admin/company/activate/<int:id>')
def activate_company(id):
    user = User.query.get_or_404(id)
    user.is_blacklisted = False
    db.session.commit()
    flash("Company activated", "success")
    return redirect(url_for('admin_companies'))

@app.route('/admin/student/deactivate/<int:id>')
def deactivate_student(id):
    user = User.query.get_or_404(id)
    user.is_blacklisted = True
    db.session.commit()
    flash("Student blacklisted", "success")
    return redirect('/admin/students')

@app.route('/admin/student/activate/<int:id>')
def activate_student(id):
    user = User.query.get(id)
    user.is_blacklisted = False
    flash("Student activated", "success")
    db.session.commit()
    return redirect('/admin/students') 

@app.route('/admin/company/search')
def admin_company_search():
    search = request.args.get('search', '').strip()

    query = (
        Company.query
        .join(User, Company.user_id == User.id)
        .filter(User.user_type == 'company', User.approval_status == 'approved')
    )

    if search:
        query = query.filter(or_(
            Company.companyname.contains(search),
            Company.hr_name.contains(search),
            Company.hr_contact.contains(search),
            User.email.contains(search),
            cast(Company.user_id, String).contains(search)
        ))

    companies = query.all()
    return render_template('admin/company.html', companies=companies)



@app.route('/admin/student/search')
def admin_student_search():
    search = request.args.get('search')
    query = (
        Student.query
        .join(User, Student.user_id == User.id)
        .filter(
            User.user_type == 'student',
            User.approval_status == 'approved'
        )
    )
    if search:
        query = query.filter(
            or_(
                Student.studentname.contains(search),
                Student.institution.contains(search),
                User.email.contains(search),
                cast(Student.user_id, String).contains(search)
            )
        )

    students = query.all()
    return render_template('admin/student.html', students=students)

@app.route('/admin/placements')
def admin_placements():
    placements = Placement.query.all()
    return render_template('admin/placement.html', placements=placements)

@app.route('/admin/applications')
def admin_applications():
    search = request.args.get('search')

    query = Application.query

    if search:
        query = (
            query
            .join(Student)
            .join(User, Student.user_id == User.id)
            .join(Placement)
            .join(Company)
            .filter(
                or_(
                    Student.studentname.contains(search),
                    User.email.contains(search),
                    Company.companyname.contains(search),
                    Placement.role.contains(search)
                )
            )
        )

    applications = query.all()

    return render_template('admin/application.html', applications=applications)

@app.route('/admin/student/<int:id>')
def admin_view_student(id):
    student = (
        Student.query
        .join(User, Student.user_id == User.id)
        .filter(User.id == id)
        .first_or_404()
    )

    return render_template('student/profile.html', student=student)

@app.route('/admin/placement/search')
def admin_placement_search():
    search = request.args.get('search')

    if search:
        students = User.query.filter(
            User.user_type == 'student',
            User.approval_status == 'approved',
            (
            (User.email.contains(search)) |
            (User.id == search)
        )).all()
    else:
        students = User.query.filter_by(user_type='student', approval_status='approved').all()

    return render_template('/admin/placement.html', students=students)

@app.route('/admin/placement/<int:id>/approve')
def approve_placement(id):
    placement = Placement.query.get_or_404(id)
    placement.approval_status = 'approved'
    db.session.commit()
    flash('Placement approved', 'success')
    return redirect(url_for('admin_placements'))


@app.route('/admin/placement/<int:id>/reject')
def reject_placement(id):
    placement = Placement.query.get_or_404(id)
    placement.approval_status = 'rejected'
    db.session.commit()
    flash('Placement rejected', 'warning')
    return redirect(url_for('admin_placements'))

@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'company':
        flash('Unauthorized access', 'danger')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    company = Company.query.filter_by(user_id=user_id).first()
    placements = Placement.query.filter_by(company_id=company.user_id).all()
    applications = Application.query.join(Placement).filter(Placement.company_id == user_id).all()
    return render_template('company/company_dash.html', company=company, placements=placements, applications=applications)

@app.route('/company/profile', methods=['GET', 'POST'])
def company_profile():
    if 'user_id' not in session or session.get('user_type') != 'company':
        return redirect(url_for('login'))

    company = Company.query.filter_by(user_id=session['user_id']).first_or_404()
    user = User.query.get_or_404(session['user_id'])

    if request.method == 'POST':
        company.companyname = request.form.get('companyname')
        company.hr_name = request.form.get('hr_name')
        company.hr_contact = request.form.get('hr_contact')

        # optional: allow email edit
        user.email = request.form.get('email')

        db.session.commit()
        flash('Company profile updated', 'success')
        return redirect(url_for('company_profile'))

    return render_template('company/profile.html', company=company, user=user)

@app.route('/company/job/new', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        job = Placement(
            role=request.form.get('role'),
            eligibility=request.form.get('eligibility'),
            description=request.form.get('description'),
            salary=request.form.get('salary'),
            skills=request.form.get('skills'),
            company_id=session['user_id'],
            status='open'
        )

        db.session.add(job)
        db.session.commit()

        flash('Job posted successfully', 'success')
        return redirect(url_for('company_dashboard'))

    return render_template('company/post.html')

@app.route('/company/job/close/<int:id>')
def close_job(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    job = Placement.query.get_or_404(id)
    job.status = 'closed'
    db.session.commit()
    return redirect(url_for('company_dashboard'))


@app.route('/company/job/activate/<int:id>')
def activate_job(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    job = Placement.query.get_or_404(id)
    job.status = 'active'
    db.session.commit()
    return redirect(url_for('company_dashboard'))

@app.route('/company/applications')
def view_applications():
    all_applications = (
        Application.query
        .join(Placement)
        .filter(Placement.company_id == session['user_id'])
        .all()
    )

    shortlisted_applications = (
        Application.query
        .join(Placement)
        .filter(
            Placement.company_id == session['user_id'],
            Application.status == 'shortlisted'
        )
        .all()
    )

    return render_template(
        'company/applications.html',
        applications=all_applications,
        shortlisted_applications=shortlisted_applications
    )

@app.route('/application/shortlist/<int:id>')
def shortlist_student(id):
    application = Application.query.get_or_404(id)
    application.status = 'shortlisted'
    db.session.commit()
    return redirect(request.referrer)

@app.route('/application/reject/<int:id>')
def reject_student(id):
    application = Application.query.get_or_404(id)
    application.status = 'rejected'
    db.session.commit()
    return redirect(request.referrer)



@app.route('/student/dashboard')
def student_dash():

    if 'user_id' not in session or session.get('user_type') != 'student':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    student_id = session['user_id']

    applications = Application.query.filter_by(student_id=student_id).all()

    total_applied = len(applications)
    shortlisted = len([a for a in applications if a.status == 'shortlisted'])
    waitlisted = len([a for a in applications if a.status == 'waitlisted'])
    rejected = len([a for a in applications if a.status == 'rejected'])

    return render_template(
        '/student/dash.html',
        total_applied=total_applied,
        shortlisted=shortlisted,
        waitlisted=waitlisted,
        rejected=rejected
    )
  
@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id=session['user_id']).first()
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        student.studentname = request.form.get('studentname')
        student.institution = request.form.get('institution')
        student.course = request.form.get('course')
        student.year_of_study = request.form.get('year_of_study')
        student.cgpa = request.form.get('cgpa')
        student.resume_link = request.form.get('resume_link')
        user.email = request.form.get('email')

        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('student_profile'))

    return render_template('student/profile.html', student=student, user=user)

@app.route('/student/apply/<int:placement_id>', methods=['GET', 'POST'])
def apply_job(placement_id):

    if 'user_id' not in session or session.get('user_type') != 'student':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    placement = Placement.query.get_or_404(placement_id)

    if request.method == 'POST':
        resume = request.form['resume']

        existing = Application.query.filter_by(
            student_id=session['user_id'],
            placement_id=placement_id
        ).first()

        if existing:
            flash("You already applied for this job!", "warning")
            return redirect(url_for('student_jobs'))

        new_application = Application(
            student_id=session['user_id'],
            placement_id=placement_id,
            resume=resume,
            status='applied'
        )

        db.session.add(new_application)
        db.session.commit()

        flash("Application submitted successfully!", "success")
        return redirect(url_for('student_applied'))

    return render_template('student/apply_form.html', placement=placement)

@app.route('/student/jobs')
def student_jobs():

    if 'user_id' not in session or session.get('user_type') != 'student':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))

    placements = Placement.query.filter_by(approval_status='approved').all()

    return render_template(
        'student/jobs.html',
        placements=placements
    )

@app.route('/student/applied')
def student_applied():
    if 'user_id' not in session or session.get('user_type') != 'student':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
        student = Student.query.filter_by(user_id=session['user_id']).first()

    applications = Application.query.filter_by(
        student_id=Student.user_id).all()

    return render_template(
        'student/applied_jobs.html',
        applications=applications
    )

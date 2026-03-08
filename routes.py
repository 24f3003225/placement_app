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
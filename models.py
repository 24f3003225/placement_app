from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)
    approval_status = db.Column(db.String(20), default='pending')
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    adminname = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Company(db.Model):
    companyname = db.Column(db.String(80), nullable=False)
    hr_name = db.Column(db.String(100), nullable=False)
    hr_contact = db.Column(db.String(15), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User',backref=db.backref('company', uselist=False))


class Student(db.Model):
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),primary_key=True)
    studentname = db.Column(db.String(80), nullable=False)
    institution = db.Column(db.String(150), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    year_of_study = db.Column(db.Integer, nullable=False)
    resume_link = db.Column(db.String(200))
    cgpa = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('student', uselist=False))


class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    salary = db.Column(db.String(50), nullable=False)
    eligibility = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    company_id = db.Column(db.Integer, db.ForeignKey('company.user_id'), nullable=False)
    status = db.Column(db.String(20), default='open')
    approval_status= db.Column(db.String(20), default='pending')
    company = db.relationship('Company', backref='placements')


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.user_id'), nullable=False)
    placement_id = db.Column(db.Integer, db.ForeignKey('placement.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')
    resume = db.Column(db.String(255), nullable=False) 
    student = db.relationship('Student', backref='applications')
    placement = db.relationship('Placement', backref='applications')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'placement_id', name='unique_student_placement'),
    )


class PlacementHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.user_id'))
    company_id = db.Column(db.Integer, db.ForeignKey('company.user_id'))
    placement_id = db.Column(db.Integer, db.ForeignKey('placement.id'))
    skills= db.Column(db.String(200))
    role = db.Column(db.String(100))
    salary = db.Column(db.String(100))

from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Admin
from werkzeug.security import generate_password_hash, check_password_hash
import models
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()
    
def create_preexisting_admin():
    admin_email = "admin@gmail.com"

    existing_user = User.query.filter_by(email=admin_email).first()
    if not existing_user:
        user = User(
            email=admin_email,
            password=generate_password_hash("admin123"),
            user_type="admin",
            approval_status="approved",
            is_blacklisted=False
        )
        db.session.add(user)
        db.session.commit()

    existing_admin = Admin.query.filter_by(email=admin_email).first()
    if not existing_admin:
        admin = Admin(
            adminname="Admin",
            email=admin_email,
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()

from routes import *
with app.app_context():
    db.create_all()
    create_preexisting_admin()

migrate = Migrate(app, db)
    
if __name__ == "__main__":
    app.run()
import os

os.environ["DATABASE_URL"] = (
    "mssql+pyodbc://@DESKTOP-OH99USR/ExamAI"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
    "&Encrypt=no"
)

from app import app
from extensions import db
from models import User
from werkzeug.security import check_password_hash

with app.app_context():
    print("Using DB:", app.config["SQLALCHEMY_DATABASE_URI"])

    print("Dropping old tables...")
    db.drop_all()

    print("Creating tables from models.py...")
    db.create_all()

    admin = User(name="System Admin", email="admin@example.com", role="admin")
    admin.set_password("Admin@12345")

    teacher = User(name="Demo Teacher", email="teacher@example.com", role="teacher")
    teacher.set_password("Teacher@12345")

    db.session.add_all([admin, teacher])
    db.session.commit()

    saved_admin = User.query.filter_by(email="admin@example.com").first()
    print("Admin saved:", saved_admin.email)
    print("Password test:", check_password_hash(saved_admin.password_hash, "Admin@12345"))

    print("Database reset finished successfully.")
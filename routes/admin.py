from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from models import Course, Document, Exam, GeneratedQuestion, User
from routes.guards import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@roles_required("admin")
def dashboard():
    stats = {
        "courses": db.session.query(Course).count(),
        "documents": db.session.query(Document).count(),
        "questions": db.session.query(GeneratedQuestion).count(),
        "exams": db.session.query(Exam).count(),
        "teachers": db.session.query(User).filter_by(role="teacher").count(),
        "students": db.session.query(User).filter_by(role="student").count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/students", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def students():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email:
            flash("Student name and email are required.", "danger")
        elif len(password) < 8:
            flash("Student password must contain at least 8 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("That email address is already registered.", "danger")
        else:
            student = User(name=name, email=email, role="student")
            student.set_password(password)
            db.session.add(student)
            db.session.commit()
            flash("Student account created.", "success")
            return redirect(url_for("admin.students"))
    return render_template(
        "admin/students.html",
        students=User.query.filter_by(role="student").order_by(User.name).all(),
    )

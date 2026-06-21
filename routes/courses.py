from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from models import Course, User
from routes.guards import roles_required

courses_bp = Blueprint("courses", __name__, url_prefix="/courses")


@courses_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def index():
    return render_template("courses/index.html", courses=Course.query.order_by(Course.created_at.desc()).all())


@courses_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def create():
    teachers = User.query.filter_by(role="teacher").order_by(User.name).all()
    if request.method == "POST":
        course = Course(
            title=request.form["title"].strip(),
            code=request.form["code"].strip(),
            description=request.form.get("description", "").strip(),
            teacher_id=request.form.get("teacher_id") or None,
        )
        db.session.add(course)
        db.session.commit()
        flash("Course created.", "success")
        return redirect(url_for("courses.index"))
    return render_template("courses/form.html", course=None, teachers=teachers)


@courses_bp.route("/<int:course_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin")
def edit(course_id):
    course = Course.query.get_or_404(course_id)
    teachers = User.query.filter_by(role="teacher").order_by(User.name).all()
    if request.method == "POST":
        course.title = request.form["title"].strip()
        course.code = request.form["code"].strip()
        course.description = request.form.get("description", "").strip()
        course.teacher_id = request.form.get("teacher_id") or None
        db.session.commit()
        flash("Course updated.", "success")
        return redirect(url_for("courses.index"))
    return render_template("courses/form.html", course=course, teachers=teachers)


@courses_bp.route("/<int:course_id>/delete", methods=["POST"])
@login_required
@roles_required("admin")
def delete(course_id):
    db.session.delete(Course.query.get_or_404(course_id))
    db.session.commit()
    flash("Course deleted.", "success")
    return redirect(url_for("courses.index"))

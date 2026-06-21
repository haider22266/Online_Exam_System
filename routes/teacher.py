from flask import Blueprint, render_template
from flask_login import current_user, login_required

from extensions import db
from models import Course, Document, Exam, GeneratedQuestion
from routes.guards import roles_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.route("/dashboard")
@login_required
@roles_required("teacher", "admin")
def dashboard():
    course_query = Course.query
    if current_user.role == "teacher":
        course_query = course_query.filter_by(teacher_id=current_user.id)
    course_ids = [course.id for course in course_query.all()]
    stats = {
        "courses": len(course_ids),
        "documents": db.session.query(Document).filter(Document.course_id.in_(course_ids)).count() if course_ids else 0,
        "questions": db.session.query(GeneratedQuestion).filter(GeneratedQuestion.course_id.in_(course_ids)).count()
        if course_ids
        else 0,
        "exams": db.session.query(Exam).filter(Exam.course_id.in_(course_ids)).count() if course_ids else 0,
    }
    return render_template("teacher/dashboard.html", stats=stats)

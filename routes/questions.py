from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Course, GeneratedQuestion
from routes.guards import roles_required
from services.question_service import QuestionGenerationService

questions_bp = Blueprint("questions", __name__, url_prefix="/questions")


@questions_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def index():
    questions = GeneratedQuestion.query.order_by(GeneratedQuestion.created_at.desc()).all()
    return render_template("questions/index.html", questions=questions)


@questions_bp.route("/generate", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def generate():
    courses = Course.query.order_by(Course.title).all()
    if request.method == "POST":
        try:
            generated = QuestionGenerationService().generate_questions(
                course_id=request.form.get("course_id", type=int),
                topic=request.form.get("topic", ""),
                count=request.form.get("count", type=int),
                difficulty=request.form.get("difficulty", "Medium"),
                question_type=request.form.get("question_type", "Multiple Choice"),
                user_id=current_user.id,
            )
            flash(f"Generated {len(generated)} questions.", "success")
            return redirect(url_for("questions.index"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            flash("Question generation failed. Check application logs.", "danger")
            raise
    return render_template("questions/generate.html", courses=courses)

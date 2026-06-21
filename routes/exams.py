from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Course, Exam, StudentExamAttempt
from routes.guards import roles_required
from services.exam_service import ExamBuilderService
from services.online_exam_service import OnlineExamService
from services.pdf_service import PdfExportService

exams_bp = Blueprint("exams", __name__, url_prefix="/exams")


@exams_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def index():
    return render_template("exams/index.html", exams=Exam.query.order_by(Exam.created_at.desc()).all())


@exams_bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def create():
    courses = Course.query.order_by(Course.title).all()
    if request.method == "POST":
        try:
            exam = ExamBuilderService().create_exam(
                course_id=request.form.get("course_id", type=int),
                title=request.form["title"].strip(),
                easy_count=request.form.get("easy_count", type=int, default=0),
                medium_count=request.form.get("medium_count", type=int, default=0),
                hard_count=request.form.get("hard_count", type=int, default=0),
                user_id=current_user.id,
                exam_type=request.form.get("exam_type", "mcq"),
                duration_minutes=request.form.get("duration_minutes", type=int, default=30),
                is_published=bool(request.form.get("is_published")),
            )
            flash("Exam created.", "success")
            return redirect(url_for("exams.detail", exam_id=exam.id))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    return render_template("exams/create.html", courses=courses)


@exams_bp.route("/<int:exam_id>")
@login_required
@roles_required("admin", "teacher")
def detail(exam_id):
    return render_template("exams/detail.html", exam=Exam.query.get_or_404(exam_id))


@exams_bp.post("/<int:exam_id>/publish")
@login_required
@roles_required("admin", "teacher")
def publish(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not exam.online_settings:
        flash("This older exam has no online settings. Create a new online exam.", "danger")
        return redirect(url_for("exams.detail", exam_id=exam.id))
    exam.online_settings.is_published = not exam.online_settings.is_published
    db.session.commit()
    state = "published" if exam.online_settings.is_published else "unpublished"
    flash(f"Exam {state}.", "success")
    return redirect(url_for("exams.detail", exam_id=exam.id))


@exams_bp.get("/<int:exam_id>/attempts")
@login_required
@roles_required("admin", "teacher")
def attempts(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    return render_template(
        "exams/attempts.html",
        exam=exam,
        attempts=StudentExamAttempt.query.filter_by(exam_id=exam.id)
        .order_by(StudentExamAttempt.started_at.desc())
        .all(),
    )


@exams_bp.route("/attempts/<int:attempt_id>/review", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def review_attempt(attempt_id):
    attempt = StudentExamAttempt.query.get_or_404(attempt_id)
    if request.method == "POST":
        try:
            OnlineExamService().grade_written_attempt(attempt, request.form)
            flash("Written exam graded.", "success")
            return redirect(url_for("exams.attempts", exam_id=attempt.exam_id))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
    answers = sorted(
        attempt.answers,
        key=lambda answer: answer.exam_question.sort_order,
    )
    return render_template("exams/review_attempt.html", attempt=attempt, answers=answers)


@exams_bp.route("/<int:exam_id>/paper.pdf")
@login_required
@roles_required("admin", "teacher")
def paper_pdf(exam_id):
    path = PdfExportService().export_exam_paper(Exam.query.get_or_404(exam_id))
    return send_file(path, as_attachment=True)


@exams_bp.route("/<int:exam_id>/answers.pdf")
@login_required
@roles_required("admin", "teacher")
def answers_pdf(exam_id):
    path = PdfExportService().export_answer_key(Exam.query.get_or_404(exam_id))
    return send_file(path, as_attachment=True)

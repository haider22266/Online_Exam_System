from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Exam, OnlineExamSettings, StudentExamAttempt
from routes.guards import roles_required
from services.online_exam_service import OnlineExamService, parse_mcq_question


student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@login_required
@roles_required("student")
def dashboard():
    published_exams = (
        Exam.query.join(Exam.online_settings)
        .filter(OnlineExamSettings.is_published == True)
        .order_by(Exam.created_at.desc())
        .all()
    )
    attempts = {
        attempt.exam_id: attempt
        for attempt in StudentExamAttempt.query.filter_by(student_id=current_user.id).all()
    }
    return render_template(
        "student/dashboard.html",
        exams=published_exams,
        attempts=attempts,
    )


@student_bp.post("/exams/<int:exam_id>/start")
@login_required
@roles_required("student")
def start_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if not exam.online_settings or not exam.online_settings.is_published:
        flash("This exam is not available.", "danger")
        return redirect(url_for("student.dashboard"))
    attempt = OnlineExamService().start_attempt(exam, current_user.id)
    if attempt.status != "in_progress":
        return redirect(url_for("student.result", attempt_id=attempt.id))
    return redirect(url_for("student.take_exam", attempt_id=attempt.id))


@student_bp.route("/attempts/<int:attempt_id>", methods=["GET", "POST"])
@login_required
@roles_required("student")
def take_exam(attempt_id):
    attempt = StudentExamAttempt.query.get_or_404(attempt_id)
    if attempt.student_id != current_user.id:
        return ("Forbidden", 403)
    if attempt.status != "in_progress":
        return redirect(url_for("student.result", attempt_id=attempt.id))

    service = OnlineExamService()
    remaining_seconds = service.remaining_seconds(attempt)
    if request.method == "POST" or remaining_seconds <= 0:
        service.submit_attempt(attempt, request.form)
        flash("Exam submitted successfully.", "success")
        return redirect(url_for("student.result", attempt_id=attempt.id))

    questions = []
    is_mcq = attempt.exam.online_settings.exam_type == "mcq"
    for item in sorted(attempt.exam.exam_questions, key=lambda row: row.sort_order):
        stem, options = parse_mcq_question(item.question.question)
        questions.append(
            {
                "item": item,
                "stem": stem if is_mcq else item.question.question,
                "options": options,
            }
        )
    return render_template(
        "student/take_exam.html",
        attempt=attempt,
        questions=questions,
        is_mcq=is_mcq,
        remaining_seconds=remaining_seconds,
    )


@student_bp.get("/attempts/<int:attempt_id>/result")
@login_required
@roles_required("student")
def result(attempt_id):
    attempt = StudentExamAttempt.query.get_or_404(attempt_id)
    if attempt.student_id != current_user.id:
        return ("Forbidden", 403)
    return render_template("student/result.html", attempt=attempt)

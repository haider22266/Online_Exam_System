from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models import Exam, GeneratedQuestion
from services.document_service import DocumentService
from services.exam_service import ExamBuilderService
from services.question_service import QuestionGenerationService

api_bp = Blueprint("api", __name__)


def serialize_question(question):
    return {
        "id": question.id,
        "course_id": question.course_id,
        "question": question.question,
        "answer": question.answer,
        "explanation": question.explanation,
        "difficulty": question.difficulty,
        "predicted_difficulty": question.predicted_difficulty,
        "question_type": question.question_type,
        "source_document": question.source_document,
    }


@api_bp.post("/upload")
@login_required
def upload():
    document = DocumentService().upload_and_process(
        request.files.get("file"),
        request.form.get("course_id", type=int),
        current_user.id,
    )
    return jsonify({"id": document.id, "status": document.status})


@api_bp.post("/generate-questions")
@login_required
def generate_questions():
    payload = request.get_json(silent=True) or request.form
    questions = QuestionGenerationService().generate_questions(
        course_id=int(payload.get("course_id")),
        topic=payload.get("topic", ""),
        count=int(payload.get("count", 5)),
        difficulty=payload.get("difficulty", "Medium"),
        question_type=payload.get("question_type", "Multiple Choice"),
        user_id=current_user.id,
    )
    return jsonify([serialize_question(question) for question in questions])


@api_bp.post("/create-exam")
@login_required
def create_exam():
    payload = request.get_json(silent=True) or request.form
    exam = ExamBuilderService().create_exam(
        course_id=int(payload.get("course_id")),
        title=payload.get("title", "Generated Exam"),
        easy_count=int(payload.get("easy_count", 0)),
        medium_count=int(payload.get("medium_count", 0)),
        hard_count=int(payload.get("hard_count", 0)),
        user_id=current_user.id,
    )
    return jsonify({"id": exam.id, "title": exam.title, "total_marks": exam.total_marks})


@api_bp.get("/questions")
@login_required
def questions():
    course_id = request.args.get("course_id", type=int)
    query = GeneratedQuestion.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    return jsonify([serialize_question(question) for question in query.order_by(GeneratedQuestion.created_at.desc()).all()])


@api_bp.get("/exams")
@login_required
def exams():
    return jsonify(
        [
            {
                "id": exam.id,
                "title": exam.title,
                "course_id": exam.course_id,
                "total_marks": exam.total_marks,
                "created_at": exam.created_at.isoformat(),
            }
            for exam in Exam.query.order_by(Exam.created_at.desc()).all()
        ]
    )

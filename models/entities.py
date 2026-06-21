from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

UnicodeString = db.Unicode
UnicodeText = db.UnicodeText


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(UnicodeString(120), nullable=False)
    email = db.Column(UnicodeString(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(UnicodeString(255), nullable=False)
    role = db.Column(UnicodeString(20), nullable=False, default="teacher")
    is_active_flag = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    courses = db.relationship("Course", back_populates="teacher", lazy=True)

    @property
    def is_active(self):
        return self.is_active_flag

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == "admin"


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(UnicodeString(200), nullable=False)
    code = db.Column(UnicodeString(50), unique=True, nullable=False)
    description = db.Column(UnicodeText)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    teacher = db.relationship("User", back_populates="courses")
    documents = db.relationship("Document", back_populates="course", cascade="all, delete-orphan")
    chunks = db.relationship("Chunk", back_populates="course", cascade="all, delete-orphan")
    questions = db.relationship("GeneratedQuestion", back_populates="course", cascade="all, delete-orphan")
    exams = db.relationship("Exam", back_populates="course", cascade="all, delete-orphan")


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    original_filename = db.Column(UnicodeString(255), nullable=False)
    stored_filename = db.Column(UnicodeString(255), nullable=False)
    file_path = db.Column(UnicodeString(500), nullable=False)
    file_type = db.Column(UnicodeString(20), nullable=False)
    page_count = db.Column(db.Integer, default=0)
    status = db.Column(UnicodeString(30), nullable=False, default="uploaded")
    error_message = db.Column(UnicodeText)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="documents")
    uploaded_by = db.relationship("User")
    chunks = db.relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(db.Model):
    __tablename__ = "chunks"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    source_file = db.Column(UnicodeString(255), nullable=False)
    page_number = db.Column(db.Integer, nullable=True)
    chunk_text = db.Column(UnicodeText, nullable=False)
    chroma_id = db.Column(UnicodeString(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="chunks")
    document = db.relationship("Document", back_populates="chunks")


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(UnicodeText, nullable=False)
    answer = db.Column(UnicodeText, nullable=False)
    difficulty = db.Column(UnicodeString(20), nullable=False)
    question_type = db.Column(UnicodeString(40), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class GeneratedQuestion(db.Model):
    __tablename__ = "generated_questions"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    question = db.Column(UnicodeText, nullable=False)
    answer = db.Column(UnicodeText, nullable=False)
    explanation = db.Column(UnicodeText)
    difficulty = db.Column(UnicodeString(20), nullable=False)
    predicted_difficulty = db.Column(UnicodeString(20))
    question_type = db.Column(UnicodeString(40), nullable=False)
    source_document = db.Column(UnicodeString(255))
    source_chunk_ids = db.Column(UnicodeText)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="questions")
    created_by = db.relationship("User")


class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False, index=True)
    title = db.Column(UnicodeString(200), nullable=False)
    total_marks = db.Column(db.Integer, nullable=False, default=0)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="exams")
    created_by = db.relationship("User")
    exam_questions = db.relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    online_settings = db.relationship(
        "OnlineExamSettings",
        back_populates="exam",
        cascade="all, delete-orphan",
        uselist=False,
    )
    attempts = db.relationship("StudentExamAttempt", back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(db.Model):
    __tablename__ = "exam_questions"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False, index=True)
    generated_question_id = db.Column(
        db.Integer,
        db.ForeignKey("generated_questions.id"),
        nullable=False,
    )
    marks = db.Column(db.Integer, nullable=False, default=1)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    exam = db.relationship("Exam", back_populates="exam_questions")
    question = db.relationship("GeneratedQuestion")
    student_answers = db.relationship(
        "StudentExamAnswer",
        back_populates="exam_question",
        cascade="all, delete-orphan",
    )


class OnlineExamSettings(db.Model):
    __tablename__ = "online_exam_settings"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), unique=True, nullable=False, index=True)
    exam_type = db.Column(UnicodeString(20), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=30)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    exam = db.relationship("Exam", back_populates="online_settings")


class StudentExamAttempt(db.Model):
    __tablename__ = "student_exam_attempts"
    __table_args__ = (
        db.UniqueConstraint("exam_id", "student_id", name="uq_student_exam_attempt"),
    )

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(UnicodeString(20), nullable=False, default="in_progress")
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)
    score = db.Column(db.Integer)
    max_score = db.Column(db.Integer, nullable=False, default=0)

    exam = db.relationship("Exam", back_populates="attempts")
    student = db.relationship("User")
    answers = db.relationship(
        "StudentExamAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class StudentExamAnswer(db.Model):
    __tablename__ = "student_exam_answers"
    __table_args__ = (
        db.UniqueConstraint("attempt_id", "exam_question_id", name="uq_attempt_question_answer"),
    )

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("student_exam_attempts.id"),
        nullable=False,
        index=True,
    )
    exam_question_id = db.Column(
        db.Integer,
        db.ForeignKey("exam_questions.id"),
        nullable=False,
        index=True,
    )
    answer_text = db.Column(UnicodeText)
    awarded_marks = db.Column(db.Integer)
    is_correct = db.Column(db.Boolean)

    attempt = db.relationship("StudentExamAttempt", back_populates="answers")
    exam_question = db.relationship("ExamQuestion", back_populates="student_answers")

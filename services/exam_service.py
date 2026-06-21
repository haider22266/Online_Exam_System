from extensions import db
from models import Course, Exam, ExamQuestion, GeneratedQuestion, OnlineExamSettings
from services.online_exam_service import parse_mcq_question


class ExamBuilderService:
    MARKS = {"Easy": 1, "Medium": 2, "Hard": 3}

    def create_exam(
        self,
        course_id,
        title,
        easy_count,
        medium_count,
        hard_count,
        user_id,
        exam_type="mcq",
        duration_minutes=30,
        is_published=False,
    ):
        if not Course.query.get(course_id):
            raise ValueError("Valid course is required.")
        if exam_type not in {"mcq", "written"}:
            raise ValueError("Exam type must be MCQ or Written.")
        if duration_minutes < 1 or duration_minutes > 360:
            raise ValueError("Duration must be between 1 and 360 minutes.")
        requested = {"Easy": easy_count, "Medium": medium_count, "Hard": hard_count}
        if sum(requested.values()) <= 0:
            raise ValueError("At least one question is required.")

        selected = []
        for difficulty, count in requested.items():
            if count <= 0:
                continue
            query = GeneratedQuestion.query.filter_by(course_id=course_id, difficulty=difficulty)
            if exam_type == "mcq":
                query = query.filter(GeneratedQuestion.question_type == "Multiple Choice")
            else:
                query = query.filter(GeneratedQuestion.question_type != "Multiple Choice")
            candidates = query.order_by(GeneratedQuestion.created_at.desc()).all()
            if exam_type == "mcq":
                questions = []
                for candidate in candidates:
                    _, options = parse_mcq_question(candidate.question)
                    option_values = {option["value"] for option in options}
                    if len(options) == 4 and candidate.answer.strip() in option_values:
                        questions.append(candidate)
                    if len(questions) == count:
                        break
            else:
                questions = candidates[:count]
            if len(questions) < count:
                raise ValueError(
                    f"Not enough {difficulty} {exam_type.upper()} questions are available."
                )
            selected.extend(questions)

        exam = Exam(course_id=course_id, title=title, created_by_id=user_id)
        db.session.add(exam)
        db.session.flush()

        total = 0
        for index, question in enumerate(selected, start=1):
            marks = self.MARKS.get(question.difficulty, 1)
            total += marks
            db.session.add(
                ExamQuestion(
                    exam_id=exam.id,
                    generated_question_id=question.id,
                    marks=marks,
                    sort_order=index,
                )
            )
        exam.total_marks = total
        db.session.add(
            OnlineExamSettings(
                exam_id=exam.id,
                exam_type=exam_type,
                duration_minutes=duration_minutes,
                is_published=is_published,
            )
        )
        db.session.commit()
        return exam

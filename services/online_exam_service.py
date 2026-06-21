import re
from datetime import datetime, timedelta

from extensions import db
from models import StudentExamAnswer, StudentExamAttempt


OPTION_PATTERN = re.compile(r"^([A-D])\.\s+(.+)$")


def parse_mcq_question(question_text):
    lines = [line.strip() for line in question_text.splitlines() if line.strip()]
    stem_lines = []
    options = []
    for line in lines:
        match = OPTION_PATTERN.match(line)
        if match:
            options.append({"label": match.group(1), "text": match.group(2), "value": line})
        else:
            stem_lines.append(line)
    return " ".join(stem_lines), options


class OnlineExamService:
    def start_attempt(self, exam, student_id):
        attempt = StudentExamAttempt.query.filter_by(
            exam_id=exam.id,
            student_id=student_id,
        ).first()
        if attempt:
            return attempt

        attempt = StudentExamAttempt(
            exam_id=exam.id,
            student_id=student_id,
            max_score=exam.total_marks,
        )
        db.session.add(attempt)
        db.session.commit()
        return attempt

    @staticmethod
    def remaining_seconds(attempt):
        duration = attempt.exam.online_settings.duration_minutes
        deadline = attempt.started_at + timedelta(minutes=duration)
        return max(0, int((deadline - datetime.utcnow()).total_seconds()))

    def submit_attempt(self, attempt, form):
        if attempt.status != "in_progress":
            return attempt

        is_mcq = attempt.exam.online_settings.exam_type == "mcq"
        total_score = 0
        for exam_question in sorted(
            attempt.exam.exam_questions,
            key=lambda item: item.sort_order,
        ):
            answer_text = form.get(f"question_{exam_question.id}", "").strip()
            answer = StudentExamAnswer(
                attempt_id=attempt.id,
                exam_question_id=exam_question.id,
                answer_text=answer_text,
            )
            if is_mcq:
                answer.is_correct = answer_text == exam_question.question.answer.strip()
                answer.awarded_marks = exam_question.marks if answer.is_correct else 0
                total_score += answer.awarded_marks
            db.session.add(answer)

        attempt.submitted_at = datetime.utcnow()
        if is_mcq:
            attempt.status = "graded"
            attempt.score = total_score
        else:
            attempt.status = "submitted"
            attempt.score = None
        db.session.commit()
        return attempt

    def grade_written_attempt(self, attempt, form):
        if attempt.exam.online_settings.exam_type != "written":
            raise ValueError("Only written exams require manual grading.")
        if attempt.status not in {"submitted", "graded"}:
            raise ValueError("This attempt has not been submitted.")

        total_score = 0
        for answer in attempt.answers:
            raw_marks = form.get(f"marks_{answer.id}", "").strip()
            try:
                awarded_marks = int(raw_marks)
            except ValueError as error:
                raise ValueError("Every written answer requires numeric marks.") from error
            maximum = answer.exam_question.marks
            if awarded_marks < 0 or awarded_marks > maximum:
                raise ValueError(f"Marks must be between 0 and {maximum}.")
            answer.awarded_marks = awarded_marks
            total_score += awarded_marks

        attempt.score = total_score
        attempt.status = "graded"
        db.session.commit()
        return attempt

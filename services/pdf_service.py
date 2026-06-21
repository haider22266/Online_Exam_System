from pathlib import Path
from xml.sax.saxutils import escape

from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class PdfExportService:
    def _output_path(self, exam, suffix):
        export_dir = Path(current_app.root_path) / "exports"
        export_dir.mkdir(exist_ok=True)
        return export_dir / f"exam_{exam.id}_{suffix}.pdf"

    def export_exam_paper(self, exam):
        path = self._output_path(exam, "paper")
        styles = getSampleStyleSheet()
        story = [
            Paragraph(exam.title, styles["Title"]),
            Paragraph(f"Course: {exam.course.title}", styles["Normal"]),
            Paragraph(f"Total Marks: {exam.total_marks}", styles["Normal"]),
            Spacer(1, 16),
        ]
        for item in sorted(exam.exam_questions, key=lambda row: row.sort_order):
            question_text = escape(item.question.question).replace("\n", "<br/>")
            story.append(
                Paragraph(
                    f"{item.sort_order}. {question_text} [{item.marks} marks]",
                    styles["BodyText"],
                )
            )
            story.append(Spacer(1, 10))
        SimpleDocTemplate(str(path), pagesize=A4).build(story)
        return path

    def export_answer_key(self, exam):
        path = self._output_path(exam, "answers")
        styles = getSampleStyleSheet()
        story = [Paragraph(f"Answer Key: {exam.title}", styles["Title"]), Spacer(1, 16)]
        for item in sorted(exam.exam_questions, key=lambda row: row.sort_order):
            story.append(Paragraph(f"{item.sort_order}. {item.question.answer}", styles["BodyText"]))
            if item.question.explanation:
                story.append(Paragraph(f"Explanation: {item.question.explanation}", styles["Normal"]))
            story.append(Spacer(1, 10))
        SimpleDocTemplate(str(path), pagesize=A4).build(story)
        return path

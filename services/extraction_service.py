from pathlib import Path

import docx
from pptx import Presentation


class ExtractionService:
    def extract(self, file_path):
        extension = Path(file_path).suffix.lower()
        if extension == ".pdf":
            return self._extract_pdf(file_path)
        if extension == ".docx":
            return self._extract_docx(file_path)
        if extension == ".pptx":
            return self._extract_pptx(file_path)
        raise ValueError("Unsupported file type.")

    def _extract_pdf(self, file_path):
        try:
            import fitz
        except ImportError as exc:
            raise ValueError("PyMuPDF is not installed correctly; PDF extraction is unavailable.") from exc

        pages = []
        try:
            with fitz.open(file_path) as pdf:
                for index, page in enumerate(pdf, start=1):
                    pages.append({"page_number": index, "text": page.get_text("text")})
        except Exception as exc:
            raise ValueError("Invalid or unreadable PDF file.") from exc
        return pages

    def _extract_docx(self, file_path):
        document = docx.Document(file_path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        return [{"page_number": 1, "text": text}]

    def _extract_pptx(self, file_path):
        presentation = Presentation(file_path)
        pages = []
        for index, slide in enumerate(presentation.slides, start=1):
            lines = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    lines.append(shape.text)
            pages.append({"page_number": index, "text": "\n".join(lines)})
        return pages

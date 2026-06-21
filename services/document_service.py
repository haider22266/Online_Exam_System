import uuid
from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import Chunk, Course, Document
from services.extraction_service import ExtractionService
from services.text_splitter import split_text
from services.vector_service import VectorStoreService


class DocumentService:
    def allowed_file(self, filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

    def upload_and_process(self, file, course_id, user_id):
        if not file or not file.filename:
            raise ValueError("Missing upload file.")
        if not course_id or not Course.query.get(course_id):
            raise ValueError("Valid course is required.")
        if not self.allowed_file(file.filename):
            raise ValueError("Only PDF, DOCX, and PPTX files are supported.")

        upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
        upload_dir.mkdir(parents=True, exist_ok=True)
        original_name = secure_filename(file.filename)
        stored_name = f"{uuid.uuid4().hex}_{original_name}"
        file_path = upload_dir / stored_name
        file.save(file_path)

        document = Document(
            course_id=course_id,
            original_filename=original_name,
            stored_filename=stored_name,
            file_path=str(file_path),
            file_type=file_path.suffix.lower().lstrip("."),
            uploaded_by_id=user_id,
            status="processing",
        )
        db.session.add(document)
        db.session.commit()

        try:
            pages = ExtractionService().extract(file_path)
            document.page_count = len(pages)
            chunks_for_vector = []
            chunk_index = 0
            for page in pages:
                for chunk_text in split_text(page["text"]):
                    chunk_index += 1
                    chroma_id = f"course-{course_id}-doc-{document.id}-chunk-{chunk_index}"
                    chunk = Chunk(
                        course_id=course_id,
                        document_id=document.id,
                        chunk_index=chunk_index,
                        source_file=original_name,
                        page_number=page["page_number"],
                        chunk_text=chunk_text,
                        chroma_id=chroma_id,
                    )
                    db.session.add(chunk)
                    db.session.flush()
                    chunks_for_vector.append(
                        {
                            "chunk_id": chunk.id,
                            "document_id": document.id,
                            "source_file": original_name,
                            "page_number": page["page_number"],
                            "text": chunk_text,
                            "chroma_id": chroma_id,
                        }
                    )
            if not chunks_for_vector:
                raise ValueError("No readable text was found in the uploaded file.")
            VectorStoreService().add_chunks(course_id, chunks_for_vector)
            document.status = "indexed"
            db.session.commit()
            current_app.logger.info("Document indexed: id=%s course=%s file=%s", document.id, course_id, original_name)
            return document
        except Exception as exc:
            db.session.rollback()
            failed_document = Document.query.get(document.id)
            failed_document.status = "failed"
            failed_document.error_message = str(exc)
            db.session.commit()
            current_app.logger.exception("Document processing failed: %s", original_name)
            raise

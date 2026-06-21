from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Course, Document
from routes.guards import roles_required
from services.document_service import DocumentService

documents_bp = Blueprint("documents", __name__, url_prefix="/documents")


@documents_bp.route("/")
@login_required
@roles_required("admin", "teacher")
def index():
    return render_template("documents/index.html", documents=Document.query.order_by(Document.created_at.desc()).all())


@documents_bp.route("/upload", methods=["GET", "POST"])
@login_required
@roles_required("admin", "teacher")
def upload():
    courses = Course.query.order_by(Course.title).all()
    if request.method == "POST":
        file = request.files.get("file")
        course_id = request.form.get("course_id", type=int)
        try:
            DocumentService().upload_and_process(file, course_id, current_user.id)
            flash("Document uploaded and indexed.", "success")
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            flash("Document processing failed. Check application logs.", "danger")
            current_app.logger.exception("Document upload failed")
        return redirect(url_for("documents.index"))
    return render_template("documents/upload.html", courses=courses)

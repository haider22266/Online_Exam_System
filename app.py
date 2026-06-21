import logging
import os
from logging.handlers import RotatingFileHandler

import click
from flask import Flask, redirect, url_for
from sqlalchemy.exc import SQLAlchemyError

from config import config_by_name
from extensions import db, login_manager, migrate
from models import User


def create_app(config_name=None):
    app = Flask(__name__)
    selected_config = config_by_name.get(config_name or os.getenv("FLASK_ENV", "default"))
    app.config.from_object(selected_config)

    ensure_runtime_dirs(app)
    configure_logging(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    register_blueprints(app)
    register_commands(app)
    register_error_handlers(app)

    return app


def ensure_runtime_dirs(app):
    for key in ("UPLOAD_FOLDER", "VECTORSTORE_PATH"):
        os.makedirs(app.config[key], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["LOG_FILE"]), exist_ok=True)


def configure_logging(app):
    handler = RotatingFileHandler(app.config["LOG_FILE"], maxBytes=1_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_blueprints(app):
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.courses import courses_bp
    from routes.documents import documents_bp
    from routes.exams import exams_bp
    from routes.questions import questions_bp
    from routes.student import student_bp
    from routes.teacher import teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))


def register_commands(app):
    @app.cli.command("check-openai")
    def check_openai():
        configured = bool(app.config.get("OPENAI_API_KEY", "").strip())
        click.echo(
            "OPENAI_API_KEY is configured."
            if configured
            else "OPENAI_API_KEY is not configured. Set it in .env or the Windows environment."
        )

    @app.cli.command("init-db")
    def init_db():
        try:
            db.create_all()
            default_users = (
                ("System Admin", "admin@example.com", "admin", "Admin@12345"),
                ("Demo Teacher", "teacher@example.com", "teacher", "Teacher@12345"),
                ("Demo Student", "student@example.com", "student", "Student@12345"),
            )
            seeded = False
            for name, email, role, password in default_users:
                if User.query.filter_by(email=email).first():
                    continue
                user = User(name=name, email=email, role=role)
                user.set_password(password)
                db.session.add(user)
                seeded = True
            if seeded:
                db.session.commit()
                app.logger.info("Seeded missing default user accounts")
            print("SQL Server database tables are ready.")
        except SQLAlchemyError as error:
            db.session.rollback()
            raise click.ClickException(
                "Could not connect to SQL Server DESKTOP-OH99USR/ExamAI. "
                "Verify that SQL Server is running, the ExamAI database exists, "
                "Windows Authentication permits this user, and ODBC Driver 17 for "
                "SQL Server is installed. If using ODBC Driver 18, update DATABASE_URL "
                "to include driver=ODBC+Driver+18+for+SQL+Server, "
                "TrustServerCertificate=yes, and Encrypt=no."
            ) from error


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return ("Forbidden", 403)

    @app.errorhandler(404)
    def not_found(error):
        return ("Not found", 404)

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception("Unhandled server error")
        return ("Server error", 500)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()


if __name__ == "__main__":
    app.run()

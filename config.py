import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
# Existing Windows process environment variables take precedence over .env.
load_dotenv(BASE_DIR / ".env", override=False)

DEFAULT_DATABASE_URL = (
    "mssql+pyodbc://@DESKTOP-OH99USR/ExamAI"
    "?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)


def database_url():
    configured_url = os.getenv("DATABASE_URL")
    if not configured_url:
        return DEFAULT_DATABASE_URL

    return configured_url


def openai_api_key():
    return os.getenv("OPENAI_API_KEY", "").strip()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    SQLALCHEMY_DATABASE_URI = database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    VECTORSTORE_PATH = os.getenv("VECTORSTORE_PATH", str(BASE_DIR / "vectorstore"))
    LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "application.log"))
    OPENAI_API_KEY = openai_api_key()
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    MAX_CONTENT_LENGTH = 64 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx"}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

# AI Exam Generator

Production-oriented Flask application for AI-powered exam question generation using SQL Server, SQLAlchemy, ChromaDB, SentenceTransformers, and OpenAI.

## Features

- Admin and teacher login with hashed passwords and role checks.
- Course CRUD and teacher assignment.
- PDF, DOCX, and PPTX upload with metadata storage.
- Hybrid semantic and Unicode-aware lexical retrieval with ChromaDB.
- OCR fallback for scanned Bengali/English PDFs.
- OpenAI question generation constrained to retrieved course context.
- Difficulty classifier training with TF-IDF and Random Forest.
- Balanced exam builder and ReportLab PDF export.
- Required REST API endpoints under `/api`.
- Application logging at `logs/application.log`.

## Quickstart

```powershell
cd exam_ai
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:FLASK_APP="app.py"
flask init-db
flask run
```

Open `http://127.0.0.1:5000`.

Default users after `flask init-db`:

- `admin@example.com` / `Admin@12345`
- `teacher@example.com` / `Teacher@12345`

## OpenAI

Set `OPENAI_API_KEY` in `.env` before generating questions. Upload and indexing can be tested without an OpenAI key.

## Scanned Bangla PDFs

Install Tesseract OCR and its Bengali (`ben`) language data. Ensure `tesseract`
is on `PATH`, or set `TESSERACT_CMD` in `.env`. Scanned PDFs are OCR-processed
with `ben+eng` by default. OCR can take several minutes for a large book.

After changing the embedding model or enabling OCR, upload existing documents
again so they are indexed with readable text and multilingual embeddings.

## SQL Server

Install Microsoft ODBC Driver 18 for SQL Server, create a database, then set:

```text
DATABASE_URL=mssql+pyodbc://db_user:db_password@localhost/AIExamGenerator?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

Use Flask-Migrate for schema management:

```powershell
flask db init
flask db migrate -m "initial schema"
flask db upgrade
flask init-db
```

The equivalent SQL Server schema is included in `database/schema.sql`.

## Train Difficulty Classifier

```powershell
python ml/train_difficulty.py
```

The model is saved to `models/difficulty_model.pkl`.

## APIs

- `POST /api/upload` multipart form: `course_id`, `file`
- `POST /api/generate-questions` JSON/form: `course_id`, `topic`, `count`, `difficulty`, `question_type`
- `POST /api/create-exam` JSON/form: `course_id`, `title`, `easy_count`, `medium_count`, `hard_count`
- `GET /api/questions`
- `GET /api/exams`

## Notes

The default `DATABASE_URL` uses SQLite so the project is immediately runnable in VS Code. For production, configure SQL Server, a strong `SECRET_KEY`, HTTPS, and a WSGI server.

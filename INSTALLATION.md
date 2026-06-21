# Installation Guide

1. Install Python 3.12 or newer.
2. Install Microsoft ODBC Driver 18 for SQL Server if using SQL Server.
3. For scanned PDFs, install Tesseract OCR and the Bengali (`ben`) language pack.
4. Create and activate a virtual environment.
5. Install dependencies with `pip install -r requirements.txt`.
6. Copy `.env.example` to `.env`.
7. Set `OPENAI_API_KEY` and, for production, `DATABASE_URL`.
8. Run `flask init-db`.
9. Run `python ml/train_difficulty.py` if difficulty validation is required.
10. Start the app with `flask run`.

For SQL Server deployments, use `flask db init`, `flask db migrate`, and `flask db upgrade` instead of relying on `db.create_all()`.

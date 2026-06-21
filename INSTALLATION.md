# Installation Guide

1. Install Python 3.12 or newer.
2. Install Microsoft ODBC Driver 18 for SQL Server if using SQL Server.
3. Create and activate a virtual environment.
4. Install dependencies with `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env`.
6. Set `OPENAI_API_KEY` and, for production, `DATABASE_URL`.
7. Run `flask init-db`.
8. Run `python ml/train_difficulty.py` if difficulty validation is required.
9. Start the app with `flask run`.

For SQL Server deployments, use `flask db init`, `flask db migrate`, and `flask db upgrade` instead of relying on `db.create_all()`.

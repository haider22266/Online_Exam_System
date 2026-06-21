@echo off
setlocal

cd /d "%~dp0"

set "FLASK_APP=app.py"

python -m flask check-openai
echo.

python -m flask init-db
if errorlevel 1 (
    echo.
    echo SQL Server initialization failed.
    echo Verify SQL Server DESKTOP-OH99USR is running and database ExamAI exists.
    echo Verify Windows Authentication access and ODBC Driver 17 for SQL Server.
    echo For ODBC Driver 18, update DATABASE_URL in .env with TrustServerCertificate=yes and Encrypt=no.
    pause
    exit /b 1
)

echo.
echo Starting AI Exam Generator at http://127.0.0.1:5000
echo Keep this window open. Press Ctrl+C to stop.
echo.

python -m flask run --no-reload

echo.
echo The server stopped.
pause

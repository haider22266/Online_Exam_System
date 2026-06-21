from pathlib import Path

from app import create_app
from services.difficulty_service import DifficultyClassifierService


app = create_app()

with app.app_context():
    csv_path = Path(app.root_path) / "sample_data" / "questions.csv"
    model_path = DifficultyClassifierService().train(csv_path)
    print(f"Saved difficulty model to {model_path}")

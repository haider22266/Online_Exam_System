from pathlib import Path

import joblib
import pandas as pd
from flask import current_app
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


class DifficultyClassifierService:
    def __init__(self):
        self.model_path = Path(current_app.root_path) / "models" / "difficulty_model.pkl"
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    def train(self, csv_path):
        data = pd.read_csv(csv_path)
        if "question" not in data.columns or "difficulty" not in data.columns:
            raise ValueError("questions.csv must contain question and difficulty columns.")
        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ("classifier", RandomForestClassifier(n_estimators=200, random_state=42)),
            ]
        )
        pipeline.fit(data["question"], data["difficulty"])
        joblib.dump(pipeline, self.model_path)
        return self.model_path

    def predict(self, question):
        if not self.model_path.exists():
            return None
        pipeline = joblib.load(self.model_path)
        return pipeline.predict([question])[0]

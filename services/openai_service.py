import json

from flask import current_app
from openai import OpenAI


class OpenAIQuestionClient:
    def __init__(self):
        api_key = current_app.config.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")
        self.client = OpenAI(api_key=api_key)

    def generate(self, topic, count, difficulty, question_type, contexts):
        is_multiple_choice = question_type.strip().lower() == "multiple choice"
        context_text = "\n\n".join(
            f"Source: {item['metadata'].get('source_file')} page {item['metadata'].get('page_number')}\n{item['text']}"
            for item in contexts
        )
        prompt = {
            "topic": topic,
            "count": count,
            "difficulty": difficulty,
            "question_type": question_type,
            "retrieved_context": context_text,
            "rules": [
                "Use only retrieved_context.",
                "If context is insufficient, return an empty questions array.",
                "Include source_document for every question.",
                (
                    "For Multiple Choice questions, include exactly four plausible options in an "
                    "options array, with one correct answer. Set answer to the exact text of the "
                    "correct option. Do not put the options inside the question field."
                    if is_multiple_choice
                    else "Do not include an options array for non-multiple-choice questions."
                ),
                "Return valid JSON only.",
            ],
        }
        response = self.client.chat.completions.create(
            model=current_app.config["OPENAI_MODEL"],
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate exam questions strictly from supplied retrieval context. "
                        "Return JSON with key questions containing objects: question, answer, "
                        "explanation, difficulty, question_type, source_document, and options. "
                        "For Multiple Choice, options must be an array of exactly four distinct "
                        "answer choices and answer must exactly match one option."
                    ),
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("questions", [])

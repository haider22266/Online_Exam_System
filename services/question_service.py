import json

from flask import current_app

from extensions import db
from models import Course, GeneratedQuestion
from services.difficulty_service import DifficultyClassifierService
from services.openai_service import OpenAIQuestionClient
from services.vector_service import VectorStoreService


class QuestionGenerationService:
    @staticmethod
    def _format_question(item, requested_type):
        question_text = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        question_type = item.get("question_type") or requested_type

        if requested_type.strip().lower() != "multiple choice":
            return question_text, answer, question_type

        options = item.get("options")
        if not isinstance(options, list):
            return "", "", question_type

        options = [str(option).strip() for option in options if str(option).strip()]
        if len(options) != 4 or len(set(options)) != 4 or answer not in options:
            return "", "", question_type

        labels = ("A", "B", "C", "D")
        formatted_options = "\n".join(
            f"{label}. {option}" for label, option in zip(labels, options)
        )
        correct_label = labels[options.index(answer)]
        return (
            f"{question_text}\n{formatted_options}",
            f"{correct_label}. {answer}",
            "Multiple Choice",
        )

    def generate_questions(self, course_id, topic, count, difficulty, question_type, user_id):
        if not Course.query.get(course_id):
            raise ValueError("Valid course is required.")
        if not topic.strip():
            raise ValueError("Topic is required.")
        if count < 1 or count > 50:
            raise ValueError("Question count must be between 1 and 50.")

        contexts = VectorStoreService().query(course_id, topic, top_k=8)
        if not contexts:
            raise ValueError("No relevant indexed content was found for this course/topic.")

        generated_items = OpenAIQuestionClient().generate(topic, count, difficulty, question_type, contexts)
        if not generated_items:
            raise ValueError("The retrieved context was insufficient to generate questions.")

        classifier = DifficultyClassifierService()
        source_chunk_ids = json.dumps([item["metadata"].get("chunk_id") for item in contexts])
        questions = []
        for item in generated_items[:count]:
            question_text, answer, normalized_type = self._format_question(item, question_type)
            predicted = classifier.predict(question_text)
            question = GeneratedQuestion(
                course_id=course_id,
                question=question_text,
                answer=answer,
                explanation=item.get("explanation", "").strip(),
                difficulty=item.get("difficulty") or difficulty,
                predicted_difficulty=predicted,
                question_type=normalized_type,
                source_document=item.get("source_document") or contexts[0]["metadata"].get("source_file"),
                source_chunk_ids=source_chunk_ids,
                created_by_id=user_id,
            )
            if not question.question or not question.answer:
                continue
            db.session.add(question)
            questions.append(question)
        if not questions:
            if question_type.strip().lower() == "multiple choice":
                raise ValueError(
                    "OpenAI returned no valid multiple-choice questions with four options."
                )
            raise ValueError("OpenAI returned no usable questions.")
        db.session.commit()
        current_app.logger.info("Generated %s questions for course=%s topic=%s", len(questions), course_id, topic)
        return questions

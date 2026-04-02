import random
import re
from datetime import datetime
from hashlib import sha256
from typing import Literal

from flask import current_app
from openai import OpenAI
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.attempt_model import QuizAnswer, QuizAttempt
from models.category_model import Category
from models.question_model import Question
from models.user_model import User

LEVEL_SEQUENCE = ["Easy", "Moderate", "Hard"]
LEVEL_ORDER = {level: index for index, level in enumerate(LEVEL_SEQUENCE)}


class GeneratedQuestion(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: Literal["A", "B", "C", "D"]


class GeneratedQuestionBatch(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=15)


def get_unlocked_levels(user: User) -> list[str]:
    highest_level = user.highest_unlocked_level or "Easy"
    unlocked_until = LEVEL_ORDER.get(highest_level, 0)
    return [level for level, order in LEVEL_ORDER.items() if order <= unlocked_until]


def can_access_level(user: User, level: str) -> bool:
    return level in get_unlocked_levels(user)


def get_next_level(level: str) -> str:
    current_index = LEVEL_ORDER.get(level, 0)
    return LEVEL_SEQUENCE[min(current_index + 1, len(LEVEL_SEQUENCE) - 1)]


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def build_question_hash(question_payload: dict) -> str:
    key = "||".join(
        [
            normalize_text(question_payload["question"]),
            normalize_text(question_payload["option_a"]),
            normalize_text(question_payload["option_b"]),
            normalize_text(question_payload["option_c"]),
            normalize_text(question_payload["option_d"]),
            normalize_text(question_payload["difficulty"]),
            str(question_payload["category_id"]),
        ]
    )
    return sha256(key.encode("utf-8")).hexdigest()


def get_openai_client() -> OpenAI:
    api_key = current_app.config["OPENAI_API_KEY"].strip()
    if not api_key:
        raise RuntimeError("OpenAI API key is missing. Add OPENAI_API_KEY to your .env file.")
    return OpenAI(api_key=api_key)


def generate_questions_with_ai(
    category_name: str,
    difficulty: str,
    count: int,
    existing_questions: list[str],
) -> list[GeneratedQuestion]:
    client = get_openai_client()
    dedupe_preview = "\n".join(f"- {text}" for text in existing_questions[:30]) or "- None yet"
    prompt = f"""
Generate exactly {count} unique general knowledge multiple-choice questions.

Category: {category_name}
Difficulty: {difficulty}

Rules:
- Keep questions fact-based, unambiguous, and suitable for a quiz app.
- Each question must have exactly four options.
- Only one option is correct.
- Keep option text concise.
- Avoid repeating or rephrasing any question from this existing cache:
{dedupe_preview}
- For Current Affairs, prefer broadly known recent events instead of hyper-local trivia.
- Return only the structured data requested by the schema.
""".strip()

    response = client.responses.parse(
        model=current_app.config["OPENAI_MODEL"],
        input=[
            {
                "role": "developer",
                "content": "You are a quiz generator that creates reliable MCQs for a GK quiz app.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=GeneratedQuestionBatch,
    )

    parsed = response.output_parsed
    if not parsed or not parsed.questions:
        raise RuntimeError("The AI did not return quiz questions in the expected format.")

    return parsed.questions[:count]


def create_or_reuse_question(category: Category, difficulty: str, generated: GeneratedQuestion):
    payload = {
        "question": generated.question.strip(),
        "option_a": generated.option_a.strip(),
        "option_b": generated.option_b.strip(),
        "option_c": generated.option_c.strip(),
        "option_d": generated.option_d.strip(),
        "correct_answer": generated.correct_answer.strip().upper(),
        "difficulty": difficulty,
        "category_id": category.id,
    }

    if len({payload["option_a"], payload["option_b"], payload["option_c"], payload["option_d"]}) < 4:
        return None

    payload["question_hash"] = build_question_hash(payload)
    existing = Question.query.filter_by(question_hash=payload["question_hash"]).first()
    if existing:
        return existing

    question = Question(**payload)
    db.session.add(question)
    try:
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return Question.query.filter_by(question_hash=payload["question_hash"]).first()
    return question


def ensure_question_pool(category: Category, difficulty: str, required_count: int) -> list[Question]:
    pool = (
        Question.query.filter_by(
            category_id=category.id,
            difficulty=difficulty,
            is_active=True,
        )
        .order_by(Question.created_at.desc())
        .all()
    )
    if len(pool) >= required_count:
        return pool

    missing = required_count - len(pool)
    existing_questions = [question.question for question in pool]

    for _ in range(3):
        generated_batch = generate_questions_with_ai(
            category.category_name,
            difficulty,
            max(missing, 5),
            existing_questions,
        )
        for generated in generated_batch:
            created = create_or_reuse_question(category, difficulty, generated)
            if created:
                existing_questions.append(created.question)
        db.session.commit()
        pool = (
            Question.query.filter_by(
                category_id=category.id,
                difficulty=difficulty,
                is_active=True,
            )
            .order_by(Question.created_at.desc())
            .all()
        )
        if len(pool) >= required_count:
            break
        missing = required_count - len(pool)

    if len(pool) < required_count:
        raise RuntimeError(
            f"Only {len(pool)} cached questions are available for {difficulty} {category.category_name}."
        )
    return pool


def prepare_attempt(user: User, category_id: int, level: str) -> QuizAttempt:
    if not can_access_level(user, level):
        raise ValueError(f"{level} is still locked for this user.")

    category = db.session.get(Category, category_id)
    if not category:
        raise ValueError("Selected category does not exist.")

    active_attempts = QuizAttempt.query.filter_by(user_id=user.id, status="in_progress").all()
    for attempt in active_attempts:
        finalize_attempt(attempt, status="abandoned")

    pool = ensure_question_pool(
        category,
        level,
        current_app.config["QUESTIONS_PER_QUIZ"],
    )
    selected_questions = random.sample(pool, current_app.config["QUESTIONS_PER_QUIZ"])

    attempt = QuizAttempt(
        user_id=user.id,
        category_id=category.id,
        level=level,
        total_questions=current_app.config["QUESTIONS_PER_QUIZ"],
        time_limit_seconds=current_app.config["QUIZ_TIME_LIMIT_SECONDS"],
        status="in_progress",
    )
    attempt.question_ids = [question.id for question in selected_questions]
    user.has_seen_rules = True

    db.session.add(attempt)
    db.session.commit()
    return attempt


def get_current_question(attempt: QuizAttempt):
    question_ids = attempt.question_ids
    if attempt.current_question_index >= len(question_ids):
        return None
    return db.session.get(Question, question_ids[attempt.current_question_index])


def upsert_answer(attempt: QuizAttempt, selected_option: str) -> QuizAnswer:
    question = get_current_question(attempt)
    if not question:
        raise ValueError("No active question is available for this attempt.")

    selected = (selected_option or "").strip().upper()
    if selected not in {"A", "B", "C", "D"}:
        raise ValueError("Please choose a valid answer option.")

    answer = QuizAnswer.query.filter_by(
        attempt_id=attempt.id,
        question_id=question.id,
    ).first()
    if not answer:
        answer = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            question_order=attempt.current_question_index + 1,
        )
        db.session.add(answer)

    answer.selected_option = selected
    answer.is_correct = selected == question.correct_answer
    answer.answered_at = datetime.utcnow()
    db.session.flush()
    return answer


def refresh_user_score(user_id: int) -> None:
    total_score = (
        db.session.query(func.coalesce(func.sum(QuizAttempt.score), 0))
        .filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.status.in_(["completed", "time_up", "abandoned"]),
        )
        .scalar()
    )
    user = db.session.get(User, user_id)
    user.total_score = int(total_score or 0)


def maybe_unlock_next_level(user: User, level: str, score: int) -> None:
    if score < current_app.config["PASSING_SCORE"]:
        return
    next_level = get_next_level(level)
    if LEVEL_ORDER[next_level] > LEVEL_ORDER.get(user.highest_unlocked_level, 0):
        user.highest_unlocked_level = next_level


def finalize_attempt(attempt: QuizAttempt, status: str = "completed") -> QuizAttempt:
    if attempt.status in {"completed", "time_up", "abandoned"}:
        return attempt

    question_map = {
        question.id: question
        for question in Question.query.filter(Question.id.in_(attempt.question_ids)).all()
    }
    answer_map = {
        answer.question_id: answer
        for answer in QuizAnswer.query.filter_by(attempt_id=attempt.id).all()
    }

    correct_answers = 0
    for order, question_id in enumerate(attempt.question_ids, start=1):
        question = question_map.get(question_id)
        if not question:
            continue
        answer = answer_map.get(question_id)
        if not answer:
            answer = QuizAnswer(
                attempt_id=attempt.id,
                question_id=question_id,
                selected_option="",
                is_correct=False,
                question_order=order,
            )
            db.session.add(answer)
        else:
            answer.question_order = order
            answer.is_correct = answer.selected_option == question.correct_answer

        if answer.is_correct:
            correct_answers += 1

    attempt.correct_answers = correct_answers
    attempt.total_questions = len(attempt.question_ids)
    attempt.wrong_answers = attempt.total_questions - correct_answers
    attempt.score = correct_answers
    attempt.current_question_index = attempt.total_questions
    attempt.status = status
    attempt.completed_at = datetime.utcnow()

    maybe_unlock_next_level(attempt.user, attempt.level, attempt.score)
    refresh_user_score(attempt.user_id)
    db.session.commit()
    return attempt

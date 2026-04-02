from pathlib import Path

from sqlalchemy import inspect, text

from extensions import db
from models.category_model import Category

CATEGORIES = [
    "History",
    "Science",
    "Geography",
    "Sports",
    "Current Affairs",
    "Technology",
    "Indian Polity",
]


def ensure_directories(app) -> None:
    upload_dir = Path(app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)


def sync_schema() -> None:
    inspector = inspect(db.engine)
    dialect = db.engine.dialect.name
    long_text_type = "LONGTEXT" if dialect == "mysql" else "TEXT"
    boolean_type = "BOOLEAN" if dialect == "mysql" else "INTEGER"

    expected_columns = {
        "users": {
            "password_hash": "VARCHAR(255) NOT NULL DEFAULT ''",
            "highest_unlocked_level": "VARCHAR(20) NOT NULL DEFAULT 'Easy'",
            "has_seen_rules": f"{boolean_type} NOT NULL DEFAULT 0",
            "is_admin": f"{boolean_type} NOT NULL DEFAULT 0",
        },
        "questions": {
            "question_hash": "VARCHAR(64) NOT NULL DEFAULT ''",
            "generated_by_ai": f"{boolean_type} NOT NULL DEFAULT 1",
            "is_active": f"{boolean_type} NOT NULL DEFAULT 1",
        },
        "quiz_attempts": {
            "category_id": "INT NULL",
            "correct_answers": "INT NOT NULL DEFAULT 0",
            "wrong_answers": "INT NOT NULL DEFAULT 0",
            "current_question_index": "INT NOT NULL DEFAULT 0",
            "time_limit_seconds": "INT NOT NULL DEFAULT 900",
            "status": "VARCHAR(20) NOT NULL DEFAULT 'in_progress'",
            "question_ids_raw": f"{long_text_type} NULL",
            "started_at": "DATETIME NULL",
            "completed_at": "DATETIME NULL",
        },
        "quiz_answers": {
            "question_order": "INT NOT NULL DEFAULT 0",
            "answered_at": "DATETIME NULL",
        },
    }

    for table_name, columns in expected_columns.items():
        if not inspector.has_table(table_name):
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, column_definition in columns.items():
            if column_name not in existing_columns:
                db.session.execute(
                    text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
                )

    db.session.commit()


def seed_categories() -> None:
    existing = {category.category_name for category in Category.query.all()}
    for category_name in CATEGORIES:
        if category_name not in existing:
            db.session.add(Category(category_name=category_name))
    db.session.commit()

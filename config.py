import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@127.0.0.1:3306/quiz_app",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=6)

    QUESTIONS_PER_QUIZ = 10
    QUIZ_TIME_LIMIT_SECONDS = 15 * 60
    PASSING_SCORE = 6

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    ADMIN_NAME = os.getenv("ADMIN_NAME", "Quiz Admin")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@aigkquiz.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@12345")

    MAX_CONTENT_LENGTH = 3 * 1024 * 1024
    UPLOAD_FOLDER = BASE_DIR / "static" / "profile_pics"
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

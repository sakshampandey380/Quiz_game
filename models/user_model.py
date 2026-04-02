from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_image = db.Column(
        db.String(255),
        nullable=False,
        default="images/default-avatar.svg",
    )
    total_score = db.Column(db.Integer, nullable=False, default=0)
    highest_unlocked_level = db.Column(db.String(20), nullable=False, default="Easy")
    has_seen_rules = db.Column(db.Boolean, nullable=False, default=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    quiz_attempts = db.relationship(
        "QuizAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def get_id(self) -> str:
        return f"user:{self.id}"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

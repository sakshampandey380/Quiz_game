import json
from datetime import datetime, timedelta

from extensions import db


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )
    level = db.Column(db.String(20), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=10)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    wrong_answers = db.Column(db.Integer, nullable=False, default=0)
    current_question_index = db.Column(db.Integer, nullable=False, default=0)
    time_limit_seconds = db.Column(db.Integer, nullable=False, default=900)
    status = db.Column(db.String(20), nullable=False, default="in_progress", index=True)
    question_ids_raw = db.Column(db.Text, nullable=False, default="[]")
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="quiz_attempts")
    category = db.relationship("Category", back_populates="quiz_attempts")
    answers = db.relationship(
        "QuizAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    @property
    def question_ids(self):
        try:
            return json.loads(self.question_ids_raw or "[]")
        except json.JSONDecodeError:
            return []

    @question_ids.setter
    def question_ids(self, question_ids):
        self.question_ids_raw = json.dumps(question_ids)

    @property
    def expires_at(self):
        return self.started_at + timedelta(seconds=self.time_limit_seconds)

    @property
    def is_expired(self):
        return datetime.utcnow() >= self.expires_at


class QuizAnswer(db.Model):
    __tablename__ = "quiz_answers"
    __table_args__ = (
        db.UniqueConstraint("attempt_id", "question_id", name="uq_attempt_question"),
    )

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_attempts.id"),
        nullable=False,
        index=True,
    )
    question_id = db.Column(
        db.Integer,
        db.ForeignKey("questions.id"),
        nullable=False,
        index=True,
    )
    selected_option = db.Column(db.String(1), nullable=False, default="")
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    question_order = db.Column(db.Integer, nullable=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    attempt = db.relationship("QuizAttempt", back_populates="answers")
    question = db.relationship("Question", back_populates="answers")

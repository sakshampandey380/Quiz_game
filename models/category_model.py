from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(80), unique=True, nullable=False)

    questions = db.relationship("Question", back_populates="category", lazy="dynamic")
    quiz_attempts = db.relationship("QuizAttempt", back_populates="category", lazy="dynamic")

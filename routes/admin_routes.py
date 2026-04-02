from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from extensions import db
from models.admin_model import AdminUser
from models.attempt_model import QuizAttempt
from models.category_model import Category
from models.question_model import Question
from models.user_model import User
from utils.auth_helper import admin_required
from utils.quiz_logic import build_question_hash

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin = AdminUser.query.filter_by(email=email).first()

        if not admin or not admin.check_password(password):
            flash("Invalid admin credentials.", "error")
        else:
            login_user(admin)
            flash("Admin session started.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html", hide_header=True)


@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3:
            flash("Admin username must be at least 3 characters long.", "error")
        elif "@" not in email:
            flash("Please enter a valid admin email address.", "error")
        elif len(password) < 8:
            flash("Admin password must be at least 8 characters long.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first():
            flash("That username or email is already in use.", "error")
        else:
            admin = AdminUser(
                username=username,
                email=email,
            )
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            login_user(admin)
            flash("Admin account created successfully.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/register.html", hide_header=True)


@admin_bp.route("/logout")
@admin_required
def admin_logout():
    logout_user()
    flash("Admin logged out.", "info")
    return redirect(url_for("admin.login"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = {
        "users": User.query.count(),
        "admins": AdminUser.query.count(),
        "questions": Question.query.count(),
        "attempts": QuizAttempt.query.count(),
        "avg_score": db.session.query(func.coalesce(func.avg(QuizAttempt.score), 0)).scalar() or 0,
    }
    recent_attempts = QuizAttempt.query.order_by(QuizAttempt.started_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    return render_template(
        "admin/admin_dashboard.html",
        stats=stats,
        recent_attempts=recent_attempts,
        recent_users=recent_users,
    )


@admin_bp.route("/questions")
@admin_required
def manage_questions():
    difficulty = request.args.get("difficulty", "").strip().title()
    category_id = request.args.get("category_id", type=int)

    query = Question.query.order_by(Question.created_at.desc())
    if difficulty in {"Easy", "Moderate", "Hard"}:
        query = query.filter_by(difficulty=difficulty)
    if category_id:
        query = query.filter_by(category_id=category_id)

    questions = query.all()
    categories = Category.query.order_by(Category.category_name.asc()).all()
    return render_template(
        "admin/manage_question.html",
        questions=questions,
        categories=categories,
        selected_difficulty=difficulty,
        selected_category_id=category_id,
    )


@admin_bp.route("/questions/add", methods=["GET", "POST"])
@admin_required
def add_question():
    categories = Category.query.order_by(Category.category_name.asc()).all()

    if request.method == "POST":
        category_id = request.form.get("category_id", type=int)
        difficulty = request.form.get("difficulty", "").strip().title()
        payload = {
            "question": request.form.get("question", "").strip(),
            "option_a": request.form.get("option_a", "").strip(),
            "option_b": request.form.get("option_b", "").strip(),
            "option_c": request.form.get("option_c", "").strip(),
            "option_d": request.form.get("option_d", "").strip(),
            "correct_answer": request.form.get("correct_answer", "").strip().upper(),
            "difficulty": difficulty,
            "category_id": category_id,
            "generated_by_ai": False,
        }

        if not db.session.get(Category, category_id):
            flash("Please choose a valid category.", "error")
        elif difficulty not in {"Easy", "Moderate", "Hard"}:
            flash("Please choose a valid difficulty.", "error")
        elif payload["correct_answer"] not in {"A", "B", "C", "D"}:
            flash("Correct answer must be A, B, C, or D.", "error")
        else:
            payload["question_hash"] = build_question_hash(payload)
            if Question.query.filter_by(question_hash=payload["question_hash"]).first():
                flash("A matching question already exists in the cache.", "error")
            else:
                question = Question(**payload)
                db.session.add(question)
                db.session.commit()
                flash("Question added successfully.", "success")
                return redirect(url_for("admin.manage_questions"))

    return render_template("admin/add_question.html", categories=categories)


@admin_bp.route("/questions/<int:question_id>/toggle", methods=["POST"])
@admin_required
def toggle_question(question_id: int):
    question = db.session.get(Question, question_id)
    if not question:
        flash("Question not found.", "error")
        return redirect(url_for("admin.manage_questions"))

    question.is_active = not question.is_active
    db.session.commit()
    flash("Question visibility updated.", "success")
    return redirect(url_for("admin.manage_questions"))

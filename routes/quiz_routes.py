from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy import func

from extensions import db
from models.attempt_model import QuizAnswer, QuizAttempt
from models.category_model import Category
from models.question_model import Question
from models.user_model import User
from utils.auth_helper import user_only_required
from utils.quiz_logic import (
    finalize_attempt,
    get_current_question,
    get_unlocked_levels,
    prepare_attempt,
    upsert_answer,
)

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

LEVEL_TEMPLATES = {
    "Easy": "quiz/quiz_easy.html",
    "Moderate": "quiz/quiz_medium.html",
    "Hard": "quiz/quiz_hard.html",
}


def get_dashboard_payload():
    unlocked_levels = get_unlocked_levels(current_user)
    categories = Category.query.order_by(Category.category_name.asc()).all()
    recent_attempts = (
        QuizAttempt.query.filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .limit(8)
        .all()
    )
    per_level_rows = (
        db.session.query(
            QuizAttempt.level,
            func.coalesce(func.sum(QuizAttempt.score), 0),
            func.count(QuizAttempt.id),
        )
        .filter(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.status.in_(["completed", "time_up", "abandoned"]),
        )
        .group_by(QuizAttempt.level)
        .all()
    )
    scores_by_level = {level: 0 for level in LEVEL_TEMPLATES}
    attempts_by_level = {level: 0 for level in LEVEL_TEMPLATES}
    for level, score_total, attempt_count in per_level_rows:
        scores_by_level[level] = int(score_total or 0)
        attempts_by_level[level] = int(attempt_count or 0)

    leaderboard = (
        User.query.filter_by(is_admin=False)
        .order_by(User.total_score.desc(), User.created_at.asc())
        .limit(5)
        .all()
    )
    return {
        "categories": categories,
        "unlocked_levels": unlocked_levels,
        "recent_attempts": recent_attempts,
        "scores_by_level": scores_by_level,
        "attempts_by_level": attempts_by_level,
        "leaderboard": leaderboard,
    }


@quiz_bp.route("/dashboard")
@user_only_required
def dashboard():
    payload = get_dashboard_payload()
    active_attempt = QuizAttempt.query.filter_by(user_id=current_user.id, status="in_progress").first()
    return render_template(
        "quiz/dashboard.html",
        active_attempt=active_attempt,
        **payload,
    )


@quiz_bp.route("/rules")
@user_only_required
def rules():
    payload = get_dashboard_payload()
    return render_template("quiz/rules.html", **payload)


@quiz_bp.route("/start", methods=["POST"])
@user_only_required
def start_quiz():
    level = request.form.get("level", "Easy").strip().title()
    category_id = request.form.get("category_id", type=int)

    if level not in LEVEL_TEMPLATES:
        flash("Please choose a valid level.", "error")
        return redirect(url_for("quiz.dashboard"))

    try:
        attempt = prepare_attempt(current_user, category_id, level)
    except Exception as exc:
        flash(str(exc), "error")
        fallback_route = "quiz.rules" if not current_user.has_seen_rules else "quiz.dashboard"
        return redirect(url_for(fallback_route))

    flash(f"{level} quiz loaded successfully. Best of luck!", "success")
    return redirect(url_for("quiz.play_attempt", attempt_id=attempt.id))


@quiz_bp.route("/attempt/<int:attempt_id>")
@user_only_required
def play_attempt(attempt_id: int):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Quiz attempt not found.", "error")
        return redirect(url_for("quiz.dashboard"))

    if attempt.status in {"completed", "time_up", "abandoned"}:
        return redirect(url_for("quiz.result", attempt_id=attempt.id))

    if attempt.is_expired:
        finalize_attempt(attempt, status="time_up")
        flash("Time is up. Your quiz was auto-submitted.", "info")
        return redirect(url_for("quiz.result", attempt_id=attempt.id))

    question = get_current_question(attempt)
    if not question:
        finalize_attempt(attempt, status="completed")
        return redirect(url_for("quiz.result", attempt_id=attempt.id))

    saved_answer = QuizAnswer.query.filter_by(
        attempt_id=attempt.id,
        question_id=question.id,
    ).first()

    return render_template(
        LEVEL_TEMPLATES[attempt.level],
        attempt=attempt,
        question=question,
        saved_answer=saved_answer.selected_option if saved_answer else "",
        current_index=attempt.current_question_index + 1,
        total_questions=len(attempt.question_ids),
        progress_percent=((attempt.current_question_index + 1) / max(len(attempt.question_ids), 1)) * 100,
    )


@quiz_bp.route("/attempt/<int:attempt_id>/autosave", methods=["POST"])
@user_only_required
def autosave_answer(attempt_id: int):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id or attempt.status != "in_progress":
        return jsonify({"ok": False, "message": "Attempt is not active."}), 400

    if attempt.is_expired:
        finalize_attempt(attempt, status="time_up")
        return jsonify({"ok": False, "message": "Quiz time ended."}), 400

    payload = request.get_json(silent=True) or {}
    selected_option = payload.get("selected_option", "")

    try:
        upsert_answer(attempt, selected_option)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400

    return jsonify({"ok": True, "message": "Answer auto-saved."})


@quiz_bp.route("/attempt/<int:attempt_id>/answer", methods=["POST"])
@user_only_required
def submit_answer(attempt_id: int):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id or attempt.status != "in_progress":
        return jsonify({"ok": False, "message": "Attempt is not active."}), 400

    if attempt.is_expired:
        finalize_attempt(attempt, status="time_up")
        return jsonify(
            {
                "ok": False,
                "message": "Quiz time ended.",
                "redirect_url": url_for("quiz.result", attempt_id=attempt.id),
            }
        ), 400

    selected_option = request.form.get("selected_option", "").strip().upper()
    try:
        upsert_answer(attempt, selected_option)
        attempt.current_question_index += 1
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(exc)}), 400

    if attempt.current_question_index >= len(attempt.question_ids):
        finalize_attempt(attempt, status="completed")
        return jsonify(
            {
                "ok": True,
                "completed": True,
                "redirect_url": url_for("quiz.result", attempt_id=attempt.id),
            }
        )

    return jsonify(
        {
            "ok": True,
            "completed": False,
            "redirect_url": url_for("quiz.play_attempt", attempt_id=attempt.id),
        }
    )


@quiz_bp.route("/attempt/<int:attempt_id>/submit", methods=["POST"])
@user_only_required
def submit_attempt(attempt_id: int):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Quiz attempt not found.", "error")
        return redirect(url_for("quiz.dashboard"))

    if attempt.status == "in_progress":
        finalize_attempt(attempt, status="completed")

    return redirect(url_for("quiz.result", attempt_id=attempt.id))


@quiz_bp.route("/attempt/<int:attempt_id>/abandon", methods=["POST"])
@user_only_required
def abandon_attempt(attempt_id: int):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        return ("", 204)

    if attempt.status == "in_progress":
        finalize_attempt(attempt, status="abandoned")

    return ("", 204)


@quiz_bp.route("/result/<int:attempt_id>")
@user_only_required
def result(attempt_id: int):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Result not found.", "error")
        return redirect(url_for("quiz.dashboard"))

    answers = (
        QuizAnswer.query.filter_by(attempt_id=attempt.id)
        .order_by(QuizAnswer.question_order.asc())
        .all()
    )
    question_lookup = {
        question.id: question
        for question in Question.query.filter(Question.id.in_([answer.question_id for answer in answers])).all()
    }
    return render_template(
        "quiz/result.html",
        attempt=attempt,
        answers=answers,
        question_lookup=question_lookup,
    )


@quiz_bp.route("/leaderboard")
@user_only_required
def leaderboard():
    top_users = (
        User.query.filter_by(is_admin=False)
        .order_by(User.total_score.desc(), User.created_at.asc())
        .limit(25)
        .all()
    )
    return render_template("quiz/leaderboard.html", top_users=top_users)

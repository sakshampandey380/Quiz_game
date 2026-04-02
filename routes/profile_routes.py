from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from extensions import db
from models.attempt_model import QuizAttempt
from utils.auth_helper import user_only_required

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


def allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    )


@profile_bp.route("/", methods=["GET", "POST"])
@user_only_required
def profile():
    if request.method == "POST":
        upload = request.files.get("profile_image")
        if upload and upload.filename:
            if not allowed_file(upload.filename):
                flash("Please upload a PNG, JPG, JPEG, GIF, or WEBP file.", "error")
                return redirect(url_for("profile.profile"))

            filename = secure_filename(upload.filename)
            unique_name = f"{uuid4().hex}_{filename}"
            save_path = Path(current_app.config["UPLOAD_FOLDER"]) / unique_name
            upload.save(save_path)
            current_user.profile_image = f"profile_pics/{unique_name}"
            db.session.commit()
            flash("Profile image updated successfully.", "success")

    level_stats_rows = (
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
    level_stats = {level: {"score": 0, "attempts": 0} for level in ["Easy", "Moderate", "Hard"]}
    for level, score_total, attempts in level_stats_rows:
        level_stats[level] = {"score": int(score_total or 0), "attempts": int(attempts or 0)}

    history = (
        QuizAttempt.query.filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )
    return render_template(
        "profile/profile.html",
        level_stats=level_stats,
        history=history,
    )

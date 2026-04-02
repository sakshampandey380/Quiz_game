from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models.user_model import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def get_post_login_redirect(user: User):
    if user.is_admin:
        return url_for("admin.dashboard")
    if not user.has_seen_rules:
        return url_for("quiz.rules")
    return url_for("quiz.dashboard")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(get_post_login_redirect(current_user))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3:
            flash("Username must be at least 3 characters long.", "error")
        elif "@" not in email:
            flash("Please enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
        elif password != confirm_password:
            flash("Passwords do not match.", "error")
        elif User.query.filter((User.username == username) | (User.email == email)).first():
            flash("A user with that username or email already exists.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registration successful. Welcome to AI GK Quiz App.", "success")
            return redirect(get_post_login_redirect(user))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(get_post_login_redirect(current_user))

    if request.method == "POST":
        credential = request.form.get("credential", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username == credential) | (User.email == credential.lower())
        ).first()

        if not user or user.is_admin or not user.check_password(password):
            flash("Invalid username/email or password.", "error")
        else:
            login_user(user, remember=remember)
            flash("Welcome back. Your dashboard is ready.", "success")
            return redirect(get_post_login_redirect(user))

    return render_template("auth/login.html", admin_mode=False)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

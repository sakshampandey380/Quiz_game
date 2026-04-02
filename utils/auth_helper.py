from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in as admin first.", "info")
            return redirect(url_for("admin.login"))
        if not current_user.is_admin:
            flash("Admin access is required for that page.", "error")
            return redirect(url_for("quiz.dashboard"))
        return view(*args, **kwargs)

    return wrapped_view


def user_only_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth.login"))
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return view(*args, **kwargs)

    return wrapped_view

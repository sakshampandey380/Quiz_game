from flask import Flask, redirect, url_for

from config import Config
from extensions import db, login_manager
from models.admin_model import AdminUser
from models.user_model import User
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.profile_routes import profile_bp
from routes.quiz_routes import quiz_bp
from utils.db_helper import ensure_directories, seed_categories, sync_schema


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templets")
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def index():
        return redirect(url_for("quiz.dashboard"))

    @login_manager.user_loader
    def load_user(user_id: str):
        if ":" not in user_id:
            return db.session.get(User, int(user_id))

        account_type, raw_id = user_id.split(":", 1)
        if account_type == "admin":
            return db.session.get(AdminUser, int(raw_id))
        if account_type == "user":
            return db.session.get(User, int(raw_id))
        return None

    with app.app_context():
        ensure_directories(app)
        db.create_all()
        sync_schema()
        seed_categories()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

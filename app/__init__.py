from flask import Flask, Blueprint, session
from flask_login import LoginManager
from app.models import get_db, User


def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key_here'

    # Flask-Login Setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return User(user['user_id'],user['username'], user['email'], user['role'])
        return None

    from .admin import admin_bp
    from .contributor import contributor_bp
    from .viewer import viewer_bp
    from .auth import auth_bp
    from .viewer.api import api_bp

    app.register_blueprint(viewer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(contributor_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)

    return app




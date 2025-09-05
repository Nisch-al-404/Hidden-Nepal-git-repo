from flask import  Blueprint
from flask_login import LoginManager
from flask import current_app

contributor_bp = Blueprint('contributor',__name__,template_folder='templates',url_prefix='/contributor')
from . import routes

login_manager = LoginManager()

# Use a function to initialize the login manager with the app
def init_login_manager(app):
    login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # Fetch user from DB using user_id
    # Return a User object
    pass
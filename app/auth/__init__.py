from flask import Blueprint

auth_bp = Blueprint('auth', __name__,static_folder='static',static_url_path='static/auth/',template_folder='templates', url_prefix='/auth')
from . import routes
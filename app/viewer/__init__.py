from flask import Blueprint
viewer_bp = Blueprint('viewer', __name__, template_folder='templates', url_prefix='/')
api_bp = Blueprint('api', __name__, url_prefix='/api')
from . import routes
from . import api
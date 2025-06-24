from flask import  Blueprint

viewer_bp = Blueprint('viewer',__name__, template_folder='templates' ,url_prefix='/')
from . import routes
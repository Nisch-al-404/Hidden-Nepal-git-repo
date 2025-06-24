from flask import  Blueprint

contributor_bp = Blueprint('contributor',__name__,template_folder='templates',url_prefix='/contributor')
from . import routes
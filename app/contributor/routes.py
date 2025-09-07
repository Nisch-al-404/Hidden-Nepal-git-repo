from flask_login import login_required, current_user

from . import contributor_bp
from flask import render_template


#@contributor_bp.route('/')
#@login_required#
def contributor_dashboard():

    return render_template("contributor/contributor_dashboard.html",user=current_user)

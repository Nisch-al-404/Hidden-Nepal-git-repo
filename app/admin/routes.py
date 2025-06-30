from . import admin_bp
from flask import render_template
from flask_login import login_required

@admin_bp.route('/')
@login_required
def admin_panel():
    return render_template('admin/layout.html')

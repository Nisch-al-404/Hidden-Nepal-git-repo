from . import admin_bp
from flask import render_template

@admin_bp.route('/')
def admin_panel():
    return render_template('admin/layout.html')

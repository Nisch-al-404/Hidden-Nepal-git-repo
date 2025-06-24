from . import admin_bp
from flask import render_template

@admin_bp.route('/')
def admin_panel():
    return "welcome to admin panel"

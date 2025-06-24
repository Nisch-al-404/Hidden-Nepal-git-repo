from . import viewer_bp
from flask import render_template

@viewer_bp.route('/')
def homepage():
    return render_template("home.html")

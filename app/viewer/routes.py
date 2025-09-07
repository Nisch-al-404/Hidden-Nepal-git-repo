from . import viewer_bp
from flask import render_template
from app.models import get_images

@viewer_bp.route('/')
def homepage():
    images = get_images()
    return render_template("home.html", images=images)

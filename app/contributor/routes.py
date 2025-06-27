from flask_login import login_required, current_user

from . import contributor_bp
from flask import render_template

from flask import Blueprint, request, redirect, url_for, flash, session
from app.models import db, Place
from werkzeug.utils import secure_filename
import os
from datetime import datetime

contributor_bp = Blueprint('contributor', __name__, template_folder='templates')

UPLOAD_FOLDER = 'static/uploads/'

@contributor_bp.route('/dashboard')
def contributor_dashboard():
    return render_template('contributor/contributor_dashboard.html')

@contributor_bp.route('/add_place', methods=['GET', 'POST'])
def add_place():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        contributor_id = session.get('user_id')
        image = request.files['image']

        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)

        new_place = Place(
            name=name,
            description=description,
            latitude=latitude,
            longitude=longitude,
            image_url=image_path,
            contributor_id=contributor_id,
            status='pending',
            created_at=datetime.utcnow()
        )
        db.session.add(new_place)
        db.session.commit()
        flash("Place submitted successfully.")
        return redirect(url_for('contributor.contributor_dashboard'))

    return render_template('contributor/add_place.html')



@contributor_bp.route('/')
@login_required
def contributor_dashboard():

    return render_template("contributor/contributor_dashboard.html",user=current_user)

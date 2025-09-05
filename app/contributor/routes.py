#Merge branch 'develop' into contributor

#- Merged latest changes from develop to keep contributor branch up to date.
from flask_login import login_required, current_user
from . import contributor_bp
from flask import render_template

from flask import request,redirect, url_for, flash, session
from app.models import get_db, Place


from werkzeug.utils import secure_filename
import os
from datetime import datetime

# contributor_bp = Blueprint('contributor', __name__, template_folder='templates')

UPLOAD_FOLDER = 'static/uploads/'
@contributor_bp.route('/')
@contributor_bp.route('/dashboard')
@login_required
def contributor_dashboard():
    return render_template('contributor/contributor_dashboard.html',user=current_user)

@contributor_bp.route('/add_place', methods=['GET', 'POST'])
def add_place():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        contributor_id = session.get('user_id')
        image = request.files['image']

        if not contributor_id:
            flash("You must be logged in to submit a place.")
            return redirect(url_for('auth.login'))

        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(image_path)

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO places (name, description, latitude, longitude, image_url, contributor_id, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (name, description, latitude, longitude, image_path, contributor_id, 'pending', datetime.now())
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Place submitted successfully.")
        return redirect(url_for('contributor.contributor_dashboard'))

    return render_template('contributor/add_place.html')
    # return "hello"


@contributor_bp.route('/my_contributions')
def my_contributions():
    user_id = session.get('user_id')
    if not user_id:
        flash("Login required")
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM places WHERE contributor_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    places = cursor.fetchall()
    cursor.close()
    db.close()
    return render_template('contributor/my_contributions.html', places=places)
# Uncomment the following lines if you want to use the contributor dashboard route


# @contributor_bp.route('/')
# @login_required
# def contributor_dashboard():

#     return render_template("contributor/contributor_dashboard.html",user=current_user)

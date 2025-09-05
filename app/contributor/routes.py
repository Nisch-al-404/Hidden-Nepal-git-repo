#Merge branch 'develop' into contributor

#- Merged latest changes from develop to keep contributor branch up to date.
from flask_login import login_required, current_user
from . import contributor_bp
from flask import render_template

from flask import request,redirect, url_for, flash, session
from app.models import get_db, Place, db


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

#  Edit Place
@contributor_bp.route('/edit_place/<int:place_id>', methods=['GET', 'POST'])
def edit_place(place_id):
    place = Place.query.get_or_404(place_id)

    # Ensure only the contributor can edit + status is pending
    if place.contributor_id != session.get('user_id'):
        flash("Unauthorized access.")
        return redirect(url_for('contributor.my_contributions'))

    if place.status != "pending":
        flash("You can only edit places that are pending approval.")
        return redirect(url_for('contributor.my_contributions'))

    if request.method == 'POST':
        place.name = request.form['name']
        place.description = request.form['description']
        place.latitude = request.form['latitude']
        place.longitude = request.form['longitude']
        place.updated_at = datetime.utcnow()

        if 'image' in request.files:
            image = request.files['image']
            if image.filename:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image.save(image_path)
                place.image_url = image_path

        db.session.commit()
        flash("Place updated successfully.")
        return redirect(url_for('contributor.my_contributions'))

    return render_template('contributor/edit_place.html', place=place)

#  Delete Place
@contributor_bp.route('/delete_place/<int:place_id>', methods=['POST'])
def delete_place(place_id):
    place = Place.query.get_or_404(place_id)

    # Ensure only contributor can delete + status is pending
    if place.contributor_id != session.get('user_id'):
        flash("Unauthorized access.")
        return redirect(url_for('contributor.my_contributions'))

    if place.status != "pending":
        flash("You can only delete places that are pending approval.")
        return redirect(url_for('contributor.my_contributions'))

    db.session.delete(place)
    db.session.commit()
    flash("Place deleted successfully.")
    return redirect(url_for('contributor.my_contributions'))

# Uncomment the following lines if you want to use the contributor dashboard route


# @contributor_bp.route('/')
# @login_required
# def contributor_dashboard():

#     return render_template("contributor/contributor_dashboard.html",user=current_user)

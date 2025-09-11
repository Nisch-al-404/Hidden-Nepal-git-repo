#Merge branch 'develop' into contributor

#- Merged latest changes from develop to keep contributor branch up to date.
from flask_login import login_required, current_user
from . import contributor_bp
from flask import render_template
from flask import Blueprint

from flask import request,redirect, url_for, flash, session
from app.models import get_db, Place, User

from werkzeug.utils import secure_filename
import os
from datetime import datetime

# contributor_bp = Blueprint('contributor', __name__, template_folder='templates')#

UPLOAD_FOLDER = "app/static/uploads/"
# @contributor_bp.route('/')
# @contributor_bp.route('/dashboard')
# @login_required
# def contributor_dashboard():
#     return render_template('contributor/contributor_layout.html',user=current_user)

@contributor_bp.route('/add_place', methods=['GET', 'POST'])
def add_place():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        contributor_id = current_user.id
        images = request.files.getlist('images')  # <-- multiple images

        if not contributor_id:
            flash("You must be logged in to submit a place.")
            return redirect(url_for('auth.login'))

        db = get_db()
        cursor = db.cursor()

        # Insert into Places table
        cursor.execute("""
            INSERT INTO Places (name, description, location, latitude, longitude, submitted_by, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, description, location, latitude, longitude, contributor_id, 'pending', datetime.now()))

        place_id = cursor.lastrowid  # get the newly created place_id

        # Handle image uploads
        for image in images:
            if image.filename == '':
                continue
            filename = secure_filename(image.filename)
            # Add timestamp for uniqueness
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
            image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            image.save(image_path)

            # Insert into Place_Images table
            cursor.execute("""
                INSERT INTO Place_Images (place_id, image_url, uploaded_at)
                VALUES (%s, %s, %s)
            """, (place_id, image_path, datetime.now()))

        db.commit()
        cursor.close()
        db.close()

        flash("Place submitted successfully and pending approval.")
        return redirect(url_for('contributor.my_contributions'))

    return render_template('contributor/add_place.html')

@contributor_bp.route('/')
@contributor_bp.route('/my_contributions')
@login_required
def my_contributions():
    user_id = current_user.id
    

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM places WHERE submitted_by = %s ORDER BY created_at DESC",
        (user_id,)
    )
    places = cursor.fetchall()
    print(places)
    cursor.close()
    db.close()
    return render_template('contributor/my_contributions.html', places=places)

#  Edit Place
@contributor_bp.route('/edit_place/<int:place_id>', methods=['GET', 'POST'])
@login_required
def edit_place(place_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # ✅ Fetch place
    cursor.execute("SELECT * FROM places WHERE place_id = %s", (place_id,))
    place = cursor.fetchone()

    if not place:
        flash("Place not found.")
        return redirect(url_for('contributor.my_contributions'))

    # ✅ Ensure only contributor can edit + status is pending
    if place['submitted_by'] != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('contributor.my_contributions'))

    if place['status'] != "pending":
        flash("You can only edit pending places.")
        return redirect(url_for('contributor.my_contributions'))

    # ✅ Fetch existing images for gallery
    cursor.execute("SELECT * FROM place_images WHERE place_id = %s", (place_id,))
    images = cursor.fetchall()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        # ✅ Update place details
        cursor.execute("""
            UPDATE places
            SET name=%s, description=%s, latitude=%s, longitude=%s
            WHERE place_id=%s
        """, (name, description, latitude, longitude, place_id))

        # ✅ Handle new images
        new_images = request.files.getlist('images')
        for image in new_images:
            if image and image.filename:
                filename = secure_filename(image.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{filename}"
                image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                image.save(image_path)

                cursor.execute("""
                    INSERT INTO place_images (place_id, image_url, uploaded_at)
                    VALUES (%s, %s, %s)
                """, (place_id, unique_filename, datetime.utcnow()))

        conn.commit()
        flash("Place updated successfully.")
        return redirect(url_for('contributor.my_contributions'))

    return render_template('contributor/edit_place.html', place=place, images=images)



# ----------------------
# Delete Place
# ----------------------
@contributor_bp.route('/delete_place/<int:place_id>', methods=['POST'])
def delete_place(place_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Fetch place
    cursor.execute("SELECT id, contributor_id, status FROM places WHERE id = %s", (place_id,))
    place = cursor.fetchone()

    if not place:
        flash("Place not found.")
        return redirect(url_for('contributor.my_contributions'))

    # Ensure only contributor can delete + status is pending
    if place['contributor_id'] != user_id:
        flash("Unauthorized access.")
        return redirect(url_for('contributor.my_contributions'))

    if place['status'] != "pending":
        flash("You can only delete places that are pending approval.")
        return redirect(url_for('contributor.my_contributions'))

    # Delete the place
    cursor.execute("DELETE FROM places WHERE id = %s", (place_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Place deleted successfully.")
    return redirect(url_for('contributor.my_contributions'))


# ----------------------
# Profile Page
# ----------------------
@contributor_bp.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to access your profile.")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get user info
    cursor.execute("""
        SELECT id, username, email, created_at 
        FROM users 
        WHERE id = %s
    """, (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("User not found.")
        return redirect(url_for('auth.login'))

    # Counts by status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM places 
        WHERE contributor_id = %s 
        GROUP BY status
    """, (user_id,))
    rows = cursor.fetchall()

    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["count"]

    total = sum(counts.values())

    # Recent submissions (last 5)
    cursor.execute("""
        SELECT id, name, status, created_at 
        FROM places 
        WHERE contributor_id = %s 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (user_id,))
    recent = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "contributor/profile.html",
        user=user,
        counts=counts,
        total=total,
        recent=recent
    )



# Uncomment the following lines if you want to use the contributor dashboard route


# @contributor_bp.route('/')
# @login_required
# def contributor_dashboard():

#     return render_template("contributor/contributor_dashboard.html",user=current_user)





#keep it at last

# contributor_bp = Blueprint('contributor', __name__, template_folder='templates')




#keep it at last


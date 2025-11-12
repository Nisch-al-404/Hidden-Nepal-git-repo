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
from flask import after_this_request

# contributor_bp = Blueprint('contributor', __name__, template_folder='templates')#

UPLOAD_FOLDER = "app/static/uploads/"
# @contributor_bp.route('/')
# @contributor_bp.route('/dashboard')
# @login_required
# def contributor_dashboard():
#     return render_template('contributor/contributor_layout.html',user=current_user)

# @contributor_bp.route('/')
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


@contributor_bp.route('/add_place', methods=['GET', 'POST'])
def add_place():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        contributor_id = current_user.id
        images = request.files.getlist('images')# <-- multiple images

        # collect selected categories (works with name="categories[]" or name="categories")
        selected_categories = request.form.getlist('categories[]') or request.form.getlist('categories')
        selected_categories = [c.strip() for c in selected_categories if c and c.strip()]

        # if categories were selected, register a post-response hook to persist them
        if selected_categories:

            @after_this_request
            def _save_categories(response):
                try:
                    conn2 = get_db()
                    cur2 = conn2.cursor(dictionary=True)

                    # find the place most recently created by this contributor in this request flow
                    cur2.execute(
                        "SELECT place_id FROM places WHERE submitted_by = %s ORDER BY created_at DESC LIMIT 1",
                        (contributor_id,)
                    )
                    row = cur2.fetchone()
                    if not row:
                        cur2.close()
                        conn2.close()
                        return response

                    place_id = row["place_id"]

                    # fetch matching category_ids for the selected names
                    placeholders = ",".join(["%s"] * len(selected_categories))
                    cur2.execute(
                        f"SELECT category_id, name FROM categories WHERE name IN ({placeholders})",
                        tuple(selected_categories)
                    )
                    rows = cur2.fetchall()
                    name_to_id = {r["name"]: r["category_id"] for r in rows}

                    # prepare insert tuples for place_categories
                    inserts = []
                    for name in selected_categories:
                        cid = name_to_id.get(name)
                        if cid:
                            inserts.append((place_id, cid))

                    if inserts:
                        # avoid duplicates with INSERT IGNORE (MySQL) or use INSERT ... ON DUPLICATE KEY if unavailable
                        cur2.executemany(
                            "INSERT IGNORE INTO place_categories (place_id, category_id) VALUES (%s, %s)",
                            inserts
                        )
                        conn2.commit()

                    cur2.close()
                    conn2.close()
                except Exception as e:
                    # don't block the response on category saving errors; log for debugging
                    print("Failed to save categories:", e)
                return response


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

    # Fetch all available categories
    cursor.execute("SELECT * FROM categories")
    all_categories = cursor.fetchall()

    # Fetch current categories for this place
    cursor.execute("""
        SELECT c.* 
        FROM categories c
        JOIN place_categories pc ON c.category_id = pc.category_id
        WHERE pc.place_id = %s
    """, (place_id,))
    current_categories = cursor.fetchall()
    print("current category",current_categories)

    if request.method == 'POST':
        place_name = request.form['name']
        description = request.form['description']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        selected_categories = request.form.getlist('categories[]') or request.form.getlist('categories')
        selected_categories = [c.strip() for c in selected_categories if c and c.strip()]

        # ✅ Update categories
        cursor.execute("DELETE FROM place_categories WHERE place_id = %s", (place_id,))
        if selected_categories:
            # Fetch category IDs for selected names
            placeholders = ",".join(["%s"] * len(selected_categories))
            cursor.execute(
                f"SELECT category_id, name FROM categories WHERE name IN ({placeholders})",
                tuple(selected_categories)
            )
            rows = cursor.fetchall()
            name_to_id = {r["name"]: r["category_id"] for r in rows}
            inserts = []
            for name in selected_categories:
                cid = name_to_id.get(name)
                if cid:
                    inserts.append((place_id, cid))
            if inserts:
                cursor.executemany(
                    "INSERT IGNORE INTO place_categories (place_id, category_id) VALUES (%s, %s)",
                    inserts
                )


        # ✅ Update place details
        cursor.execute("""
            UPDATE places
            SET name=%s, description=%s, latitude=%s, longitude=%s
            WHERE place_id=%s
        """, (place_name, description, latitude, longitude, place_id))

        try:
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
                    """, (place_id, image_path, datetime.utcnow()))
        except Exception as e:
            conn.rollback()
            flash("An error occurred while uploading images.")
            print("Image upload error:", e)

        conn.commit()
        flash("Place updated successfully.")
        return redirect(url_for('contributor.my_contributions'))

    return render_template('contributor/edit_place.html', place=place, images=images,current_categories=current_categories, all_categories=all_categories)



# ----------------------
# Delete Place
# ----------------------
@contributor_bp.route('/delete_place/<int:place_id>', methods=['POST'])
@login_required
def delete_place(place_id):
    

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Fetch place
    cursor.execute("SELECT * FROM places WHERE place_id = %s", (place_id,))
    place = cursor.fetchone()

    if not place:
        flash("Place not found.")
        return redirect(url_for('contributor.my_contributions'))

    # Ensure only contributor can delete + status is pending
    if place['submitted_by'] != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for('contributor.my_contributions'))

    if place['status'] != "pending":
        flash("You can only delete places that are pending approval.")
        return redirect(url_for('contributor.my_contributions'))

    # Delete the place
    cursor.execute("DELETE FROM places WHERE place_id = %s", (place_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Place deleted successfully.")
    return redirect(url_for('contributor.my_contributions'))
# ----------------------
# Profile Page
# ----------------------
# Contributor Profile
@contributor_bp.route('/profile')
@login_required
def profile():
    user_id = current_user.id
    if not user_id:
        flash("Please log in to access your profile.")
        return redirect(url_for('auth.login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get user info
    cursor.execute("""
        SELECT user_id, username, email, created_at 
        FROM users 
        WHERE user_id = %s
    """, (int(user_id),))
    user = cursor.fetchone()

    if not user:
        flash("User not found.")
        return redirect(url_for('auth.login'))

    # Counts by status
    cursor.execute("""
        SELECT status, COUNT(*) as count 
        FROM places 
        WHERE submitted_by = %s 
        GROUP BY status
    """, (int(user_id),))
    rows = cursor.fetchall()

    counts = {"pending": 0, "approved": 0, "rejected": 0}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] = row["count"]

    total = sum(counts.values())

    # Recent submissions (last 5)
    cursor.execute("""
        SELECT place_id, name, status, created_at 
        FROM places 
        WHERE submitted_by= %s 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (int(user_id),))
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


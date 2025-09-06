from functools import wraps
from . import admin_bp
from flask import flash, redirect, render_template,abort, url_for
from flask_login import login_required, current_user
from app.models import get_db
from flask import request

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            abort(403)  # forbidden
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_panel():
    conn=None
    cursor=None
    
    result=None
    monthly_data=None
    
    try:
    
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(" SELECT (SELECT COUNT(*) FROM users) AS total_users,(SELECT COUNT(*) FROM places) AS total_places,(SELECT COUNT(*) FROM places WHERE status='Pending') AS pending_contributor_requests,(SELECT COUNT(*) FROM places WHERE status='Approved') AS approved_places")
        result = cursor.fetchone()

        print("Total Users:", result['total_users'])
        print("Total Places:", result['total_places'])
        print("Pending Contributor Requests:", result['pending_contributor_requests'])
        print("Approved Places:", result['approved_places'])

        # cursor.execute("SELECT YEAR(created_at) AS year, MONTH(created_at) AS month, COUNT(*) AS count FROM Places WHERE YEAR(created_at) = YEAR(CURDATE()) GROUP BY YEAR(created_at), MONTH(created_at)")
        # monthly_data = cursor.fetchall()
        monthly_data = [
    
    {'year': 2024, 'month': 10, 'count': 200},
    {'year': 2024, 'month': 11, 'count': 175},
    {'year': 2024, 'month': 12, 'count': 160},
    {'year': 2025, 'month': 1, 'count': 130},
    {'year': 2025, 'month': 2, 'count': 160},
    {'year': 2025, 'month': 3, 'count': 190},
    {'year': 2025, 'month': 4, 'count': 220},
    {'year': 2025, 'month': 5, 'count': 200},
    {'year': 2025, 'month': 6, 'count': 240},
    {'year': 2025, 'month': 7, 'count': 260},
    {'year': 2025, 'month': 8, 'count': 230},
    {'year': 2025, 'month': 9, 'count': 250},
    {'year': 2025, 'month': 10, 'count': 210},
    {'year': 2025, 'month': 11, 'count': 185},
    {'year': 2025, 'month': 12, 'count': 170},
]
       
        cursor.execute("SELECT aa.action_id AS action_id, p.place_id AS place_id, p.name AS place_name, u.user_id AS contributor_id, u.username AS contributor_name, a.user_id AS admin_id, a.username AS admin_name, aa.action AS action_status, aa.action_date AS action_date, aa.notes AS action_notes FROM Admin_Actions aa JOIN Places p ON p.place_id = aa.place_id JOIN Users u ON u.user_id = p.submitted_by JOIN Users a ON a.user_id = aa.admin_id ORDER BY aa.action_date DESC LIMIT 20;")
        recent_activities=cursor.fetchall()
        print(recent_activities)

       
    except Exception as e:
        print("Admin panel error:",e)    


    return render_template('admin/dashboard.html', total_places=result['total_places'], pending_requests=result['pending_contributor_requests'], approved_places=result['approved_places'],total_users=result['total_users'],recent_activities=recent_activities,monthly_data=monthly_data,active_page='dashboard')


@admin_bp.route('manage_places',methods=['GET'])
@admin_required
@login_required
def manage_places():
    if request.method == 'GET':
        search = request.args.get('search')
        status = request.args.get('status')
        sort = request.args.get('sort')
        print("Search:",search)
        print("Status:",status)
        print("Sort:",sort)
        sort_order = 'DESC'  # Default sort order
        if sort in ['newest','oldest']:
            sort_order = 'DESC' if sort == 'newest' else 'ASC'


        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT p.place_id, p.name AS place_name, p.description, p.status, p.created_at,
                       u.user_id AS contributor_id, u.username AS contributor_name
                FROM Places p
                JOIN Users u ON p.submitted_by = u.user_id
                WHERE (%s IS NULL OR p.name LIKE %s OR u.username LIKE %s OR u.user_id=%s OR p.place_id=%s)
                  AND (%s IS NULL OR p.status = %s)
                
                """,
                (
                    search,
                    f"%{search}%",
                    f"%{search}%",
                    search,
                    search,
                    status if status in ['pending', 'approved', 'rejected'] else None,
                    status if status in ['pending', 'approved', 'rejected'] else None
                )
            )
            places = cursor.fetchall()
            print("Places:", places)
            return render_template('admin/manage_places.html',active_page='manage_places',places=places)
            
        except Exception as e:
            print("Manage places error:", e)
            places = []
    else:
        places = []
    return render_template('admin/manage_places.html',active_page='manage_places',places=places)

@admin_bp.route('manage_places/view/<int:place_id>')
@admin_required
@login_required
def view_place(place_id):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # 1. Place details + contributor info
        cursor.execute("""
            SELECT p.place_id, p.name AS place_name, p.description, p.location, 
                   p.latitude, p.longitude, p.status, p.created_at,
                   u.user_id AS contributor_id, u.username AS contributor_name, u.email AS contributor_email
            FROM Places p
            LEFT JOIN Users u ON p.submitted_by = u.user_id
            WHERE p.place_id = %s
        """, (place_id,))
        place = cursor.fetchone()

        if not place:
            flash("Place not found.", "danger")
            return redirect(url_for("admin.manage_places"))

        # 2. Place images
        cursor.execute("""
            SELECT image_id, image_url, uploaded_at
            FROM Place_Images
            WHERE place_id = %s
            ORDER BY uploaded_at DESC
        """, (place_id,))
        images = cursor.fetchall()

        # 3. Reviews with reviewer info
        cursor.execute("""
            SELECT r.review_id, r.rating, r.comment, r.created_at,
                   u.user_id, u.username
            FROM Reviews r
            JOIN Users u ON r.user_id = u.user_id
            WHERE r.place_id = %s
            ORDER BY r.created_at DESC
        """, (place_id,))
        reviews = cursor.fetchall()

    except Exception as e:
        print("Error in view_place:", e)
        flash("An error occurred while loading place details.", "danger")
        return redirect(url_for("admin.manage_places"))
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception as e:
            print("Error closing DB connection:", e)

    return render_template(
        "admin/view_place.html",
        active_page="manage_places",
        place=place,
        images=images,
        reviews=reviews,
    )

@admin_bp.route('manage_places/edit/<int:place_id>', methods=['GET', 'POST'])
@admin_required
@login_required
def edit_place(place_id):
    if request.method == 'POST':
        # Handle form submission to update place details
        name = request.form.get('name')
        description = request.form.get('description')
        location = request.form.get('location')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        status = request.form.get('status')

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE Places
                SET name=%s, description=%s, location=%s, latitude=%s, longitude=%s, status=%s
                WHERE place_id=%s
            """, (name, description, location, latitude, longitude, status, place_id))
            conn.commit()
            flash("Place updated successfully.", "success")
            return redirect(url_for('admin.view_place', place_id=place_id))
        except Exception as e:
            print("Error updating place:", e)
            flash("An error occurred while updating the place.", "danger")
        finally:
            try:
                cursor.close()
                conn.close()
            except Exception as e:
                print("Error closing DB connection:", e)
    


    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
    
        cursor.execute("""
            SELECT place_id, name, description, location, latitude, longitude, status
            FROM Places
            WHERE place_id = %s
        """, (place_id,))
        place = cursor.fetchone()
    
        if not place:
            flash("Place not found.", "danger")
            return redirect(url_for("admin.manage_places"))
    except Exception as e:
        print("Error fetching place details:", e)
        flash("An error occurred while loading place details.", "danger")
        return redirect(url_for("admin.manage_places"))
    
    return render_template('admin/edit_place.html', active_page='manage_places', place=place)
    
@admin_bp.route('manage_users')
def manage_users():
    return render_template('admin/manage_users.html')

@admin_bp.route('contributor_requests')
def contributor_requests():
    return render_template('admin/contributor_requests.html')
@admin_bp.route('settings')
def settings():
    return render_template('admin/site_settings.html')

from flask import render_template, abort, request, jsonify
from werkzeug.exceptions import HTTPException
import traceback
import json
from flask_login import current_user
from flask_login import login_required
import os
import smtplib
from email.message import EmailMessage
from app.models import get_db
from . import viewer_bp
import requests


@viewer_bp.route('/')
def homepage():
    return render_template("index.html")


@viewer_bp.route('/about')
def about():
    return render_template("about.html")

@viewer_bp.route('/contact')
def contact():
   return render_template("contact.html")

@viewer_bp.route('/faq')
def faq():
   return render_template("faq.html")

@viewer_bp.route('/places')
def places_list():
   print("Fetching places list")
   try:
      db = get_db()
      cursor = db.cursor(dictionary=True)
      category = None
      if 'category' in request.args:
         category = request.args.get('category')
      if category:
         cursor.execute("SELECT * FROM Places WHERE category = %s ORDER BY created_at DESC", (category,))
      else:
         cursor.execute("SELECT * FROM Places ORDER BY created_at DESC")
      places = cursor.fetchall()
      return render_template("places_list.html", places=places)
   except Exception as e:
      print(f"Error in places_list: {e}")
      abort(500)
   finally:
      if 'cursor' in locals():
         cursor.close()
      if 'db' in locals():
         db.close()

@viewer_bp.route('/places/<int:place_id>')
def place_detail(place_id):
    try:
        # Quick debug shortcut: if ?debug_render=1 is passed, return a tiny response
        if request.args.get('debug_render') == '1':
            return f"OK placeholder for place {place_id}", 200
        print(f"place_detail called with place_id={place_id}")
        db = get_db()
        cursor = db.cursor(dictionary=True)
        # Try to find the place by common ID column names. Some schemas use place_id, others id.
        place = None
        try:
            cursor.execute("SELECT * FROM Places WHERE place_id = %s", (place_id,))
            place = cursor.fetchone()
        except Exception:
            # ignore and try next
            place = None
        if not place:
            # try 'id' column; wrap in try/except because the column may not exist
            try:
                cursor.execute("SELECT * FROM Places WHERE id = %s", (place_id,))
                place = cursor.fetchone()
            except Exception:
                place = None
        # normalize to provide `id` to templates (many templates expect place.id)
        if place and 'place_id' in place and 'id' not in place:
            place['id'] = place['place_id']
        # load images for this place (if any)
        images = []
        if place:
            img_cursor = db.cursor(dictionary=True)
            try:
                img_cursor.execute("SELECT image_url FROM Place_Images WHERE place_id = %s ORDER BY image_id ASC", (place.get('id'),))
                rows = img_cursor.fetchall()
                images = [r.get('image_url') for r in rows if r.get('image_url')]
            except Exception:
                images = []
            finally:
                img_cursor.close()
        if not place:
            abort(404)

        # also provide a JSON string for images to embed safely in JS
        images_json = json.dumps(images or [])
        return render_template("place_detail.html", place=place, place_images=images, place_images_json=images_json)
    except Exception as e:
        # If this is an HTTPException (like abort(404)), re-raise to preserve correct status
        if isinstance(e, HTTPException):
            raise
        print(f"Error in place_detail: {e}")
        # Print full traceback to aid debugging
        tb = traceback.format_exc()
        print(tb)
        try:
            with open('place_detail_error.log', 'a', encoding='utf-8') as f:
                f.write('\n----- place_detail error -----\n')
                f.write(tb)
        except Exception:
            pass
        abort(500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@viewer_bp.route('/dbtest')
def dbtest():
    print("Testing database connection")
    try:
        db = get_db()
        
        print("Database connection established")
        cursor = db.cursor()
        print("Executing test query")
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Test query result: {result}")
        return "Database connection successful!"
    except Exception as e:
        print(f"Database connection failed: {e}")
      

@viewer_bp.route('/api')
def api_info():
    return "API is available at /api/"


@viewer_bp.route('/api/places/advanced_filter')
def advanced_filter():
    print("Advanced filter called")
    region = request.args.get('region')
    category = request.args.get('category')
    min_rating = request.args.get('min_rating', type=float)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = "SELECT * FROM places WHERE 1=1"
    params = []
    if region:
        query += " AND region = %s"
        params.append(region)
    if category:
        query += " AND category = %s"
        params.append(category)
    if min_rating is not None:
        query += " AND rating >= %s"
        params.append(min_rating)
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(results)


# Server-side contact send endpoint (trusted path for logged-in users)
@viewer_bp.route('/_internal/send_contact', methods=['POST'])
def internal_send_contact():
    # Require authentication server-side. Do NOT trust client-supplied email.
    if not getattr(current_user, 'is_authenticated', False):
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()
    name = data.get('name') or getattr(current_user, 'username', '')

    if not subject or not message:
        return jsonify({'error': 'subject and message are required'}), 400

    # Read SMTP configuration from environment variables
    SMTP_HOST = os.environ.get('CONTACT_SMTP_HOST')
    SMTP_PORT = int(os.environ.get('CONTACT_SMTP_PORT', 587)) if os.environ.get('CONTACT_SMTP_PORT') else None
    SMTP_USER = os.environ.get('CONTACT_SMTP_USER')
    SMTP_PASS = os.environ.get('CONTACT_SMTP_PASS')
    SMTP_FROM = os.environ.get('CONTACT_SMTP_FROM') or SMTP_USER
    CONTACT_RECIPIENT = os.environ.get('CONTACT_RECIPIENT', 'sapkotapawan381@gmail.com')

    if not SMTP_HOST or not SMTP_PORT or not SMTP_USER or not SMTP_PASS:
        return jsonify({'error': 'SMTP is not configured on the server'}), 500

    # Build email
    email_msg = EmailMessage()
    email_msg['Subject'] = subject
    email_msg['From'] = SMTP_FROM
    email_msg['To'] = CONTACT_RECIPIENT
    body = []
    body.append(f"You got a new message from: {name}")
    body.append(f"Time: {__import__('datetime').datetime.utcnow().isoformat()} UTC")
    body.append("")
    body.append(message)
    email_msg.set_content("\n".join(body))

    try:
        # Connect and send
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(email_msg)
        server.quit()
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        # Log and return generic error
        print(f"Error sending contact email: {e}")
        return jsonify({'error': 'Failed to send email from server'}), 500


@viewer_bp.route('/api/places/by_category')
def places_by_category():
    # Accept either category_id (int) or category name (category or category_name)
    category_id = request.args.get('category_id', type=int)
    category_name = request.args.get('category') or request.args.get('category_name')

    if not category_id and not category_name:
        return jsonify({"error": "category_id or category is required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Select one representative image per place (MIN) to avoid duplicate rows when multiple images exist
    # Join Categories to allow lookup by name
    query = """
        SELECT p.place_id, p.name, p.description, p.location,
               MIN(pi.image_url) AS image_url
        FROM Places p
        JOIN Place_Categories pc ON p.place_id = pc.place_id
        LEFT JOIN Place_Images pi ON p.place_id = pi.place_id
        LEFT JOIN Categories c ON pc.category_id = c.category_id
        WHERE p.status = 'approved'
    """
    params = []
    if category_id:
        query += " AND pc.category_id = %s"
        params.append(category_id)
    else:
        query += " AND c.name = %s"
        params.append(category_name)

    query += " GROUP BY p.place_id ORDER BY p.place_id"
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(results)

# Favorites: add/remove, get user's favorites (user_id required)
@viewer_bp.route('/api/favorites', methods=['GET', 'POST', 'DELETE'])
def favorites():
    user_id = request.args.get('user_id', type=int)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'GET':
        cursor.execute("SELECT p.* FROM favorites f JOIN places p ON f.place_id = p.id WHERE f.user_id = %s", (user_id,))
        results = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(results)
    elif request.method == 'POST':
        place_id = request.json.get('place_id')
        cursor.execute("INSERT IGNORE INTO favorites (user_id, place_id) VALUES (%s, %s)", (user_id, place_id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Added to favorites'})
    elif request.method == 'DELETE':
        place_id = request.json.get('place_id')
        cursor.execute("DELETE FROM favorites WHERE user_id = %s AND place_id = %s", (user_id, place_id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Removed from favorites'})

# Reviews: get/add for a place
# Reviews: get/add for a place (with average rating)
@viewer_bp.route('/api/reviews/<int:place_id>', methods=['GET', 'POST'])
def reviews(place_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'GET':
        # Fetch all reviews with username
        cursor.execute("""
            SELECT r.review_id, r.rating, r.comment, r.created_at, u.username
            FROM Reviews r
            JOIN Users u ON r.user_id = u.user_id
            WHERE r.place_id = %s
            ORDER BY r.created_at DESC
        """, (place_id,))
        reviews = cursor.fetchall()

        # Calculate average rating
        cursor.execute("""
            SELECT AVG(rating) as avg_rating, COUNT(*) as total_reviews
            FROM Reviews
            WHERE place_id = %s
        """, (place_id,))
        stats = cursor.fetchone()

        cursor.close()
        db.close()

        return jsonify({
            "reviews": reviews,
            "average_rating": round(stats["avg_rating"], 1) if stats["avg_rating"] else 0,
            "total_reviews": stats["total_reviews"]
        })

    elif request.method == 'POST':
        # Require authentication server-side. Do NOT trust client-supplied user_id.
        if not getattr(current_user, 'is_authenticated', False):
            cursor.close()
            db.close()
            return jsonify({'error': 'Authentication required'}), 401

        data = request.get_json() or {}
        rating = data.get('rating')
        comment = data.get('comment')

        # Use the server-side user id from current_user. Support common attribute names.
        user_id = getattr(current_user, 'id', None) or getattr(current_user, 'user_id', None)
        if not user_id:
            cursor.close()
            db.close()
            return jsonify({'error': 'Authenticated user id not available on server'}), 500

        cursor.execute("""
            INSERT INTO Reviews (place_id, user_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (place_id, user_id, rating, comment))
        db.commit()
        cursor.close()
        db.close()

        return jsonify({'message': 'Review added successfully!'})

from flask import Blueprint, jsonify, request
from app.models import get_db
import requests

api_bp = Blueprint('api', __name__, url_prefix='/api')

OPENWEATHER_API_KEY = "5d5c9b97d149189cce63766618482c70"

# Search places by name or description
@viewer_bp.route('/api/search')
def search_places():
    query = request.args.get('q', '')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM places WHERE name LIKE %s OR description LIKE %s", (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(results)

# Filter places by status
@viewer_bp.route('/api/filter')
def filter_places():
    status = request.args.get('status', 'approved')
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM places WHERE status = %s", (status,))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(results)

# Get nearby places (simple version: within latitude/longitude range)
@viewer_bp.route('/api/nearby')
def nearby_places():
    lat = float(request.args.get('lat', 0))
    lng = float(request.args.get('lng', 0))
    radius = float(request.args.get('radius', 0.1))  # degrees, not km
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM places WHERE ABS(latitude - %s) < %s AND ABS(longitude - %s) < %s", (lat, radius, lng, radius))
    results = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(results)

# Get weather for a place (dummy data, replace with real API if needed)
@viewer_bp.route('/api/weather/<int:place_id>')
def place_weather(place_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    # support either id or place_id in DB (try place_id first, then id)
    place = None
    try:
        cursor.execute("SELECT latitude, longitude FROM Places WHERE place_id = %s", (place_id,))
        place = cursor.fetchone()
    except Exception:
        place = None
    if not place:
        try:
            cursor.execute("SELECT latitude, longitude FROM Places WHERE id = %s", (place_id,))
            place = cursor.fetchone()
        except Exception:
            place = None
    cursor.close()
    db.close()
    if not place:
        return jsonify({'error': 'Place not found'}), 404

    lat, lon = place['latitude'], place['longitude']
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        weather = data['weather'][0]['main']
        description = data['weather'][0].get('description')
        temperature = data['main']['temp']
        humidity = data['main'].get('humidity')
        wind_speed = data.get('wind', {}).get('speed')
        return jsonify({
            'place_id': place_id,
            'weather': weather,
            'description': description,
            'temperature': temperature,
            'humidity': humidity,
            'wind_speed': wind_speed
        })
    else:
        return jsonify({'error': 'Weather API error'}), 500



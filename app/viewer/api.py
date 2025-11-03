from flask import Blueprint, jsonify, request
from app.models import get_db
from . import api_bp
import requests


@api_bp.route('/test')
def test():
    print("API Home accessed")
    return jsonify({'message': 'Welcome to the Places API'})
# Advanced filter: by region, category, rating
@api_bp.route('/places/advanced_filter')
def advanced_filter():
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

# Favorites: add/remove, get user's favorites (user_id required)
@api_bp.route('/favorites', methods=['GET', 'POST', 'DELETE'])
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
@api_bp.route('/reviews/<int:place_id>', methods=['GET', 'POST'])
def reviews(place_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    if request.method == 'GET':
        cursor.execute("SELECT * FROM reviews WHERE place_id = %s ORDER BY created_at DESC", (place_id,))
        results = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(results)
    elif request.method == 'POST':
        user_id = request.json.get('user_id')
        rating = request.json.get('rating')
        comment = request.json.get('comment')
        cursor.execute("INSERT INTO reviews (place_id, user_id, rating, comment) VALUES (%s, %s, %s, %s)", (place_id, user_id, rating, comment))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({'message': 'Review added'})
from flask import Blueprint, jsonify, request
from app.models import get_db
import requests

api_bp = Blueprint('api', __name__, url_prefix='/api')

OPENWEATHER_API_KEY = "5d5c9b97d149189cce63766618482c70"

# Search places by name or description
@api_bp.route('/search')
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
@api_bp.route('/filter')
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
@api_bp.route('/nearby')
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
@api_bp.route('/weather/<int:place_id>')
def place_weather(place_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT latitude, longitude FROM places WHERE id = %s", (place_id,))
    place = cursor.fetchone()
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
        temperature = data['main']['temp']
        return jsonify({
            'place_id': place_id,
            'weather': weather,
            'temperature': temperature
        })
    else:
        return jsonify({'error': 'Weather API error'}), 500

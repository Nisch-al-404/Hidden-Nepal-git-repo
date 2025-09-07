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

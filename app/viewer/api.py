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
import math

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

    # Enrich with average rating and total reviews in a single aggregated query
    try:
        place_ids = []
        id_key = None
        for r in results:
            if 'place_id' in r:
                id_key = 'place_id'
                break
            if 'id' in r:
                id_key = 'id'
                break
        if id_key:
            for r in results:
                pid = r.get(id_key)
                if pid is not None:
                    place_ids.append(pid)

        if place_ids:
            # build placeholder list
            placeholders = ','.join(['%s'] * len(place_ids))
            agg_q = f"SELECT place_id, AVG(rating) as avg_rating, COUNT(*) as total_reviews FROM Reviews WHERE place_id IN ({placeholders}) GROUP BY place_id"
            cursor.execute(agg_q, tuple(place_ids))
            aggs = cursor.fetchall()
            agg_map = {row['place_id']: row for row in aggs}
            for r in results:
                pid = r.get(id_key)
                agg = agg_map.get(pid)
                if agg:
                    r['average_rating'] = float(round(agg.get('avg_rating') or 0, 1)) if agg.get('avg_rating') is not None else None
                    r['total_reviews'] = int(agg.get('total_reviews') or 0)
                else:
                    r['average_rating'] = None
                    r['total_reviews'] = 0
    except Exception:
        # If aggregation fails, just continue without ratings
        pass

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

    # Add average rating and total reviews for each place
    try:
        place_ids = []
        id_key = None
        for r in results:
            if 'place_id' in r:
                id_key = 'place_id'
                break
            if 'id' in r:
                id_key = 'id'
                break
        if id_key:
            for r in results:
                pid = r.get(id_key)
                if pid is not None:
                    place_ids.append(pid)

        if place_ids:
            placeholders = ','.join(['%s'] * len(place_ids))
            agg_q = f"SELECT place_id, AVG(rating) as avg_rating, COUNT(*) as total_reviews FROM Reviews WHERE place_id IN ({placeholders}) GROUP BY place_id"
            cursor.execute(agg_q, tuple(place_ids))
            aggs = cursor.fetchall()
            agg_map = {row['place_id']: row for row in aggs}
            for r in results:
                pid = r.get(id_key)
                agg = agg_map.get(pid)
                if agg:
                    r['average_rating'] = float(round(agg.get('avg_rating') or 0, 1)) if agg.get('avg_rating') is not None else None
                    r['total_reviews'] = int(agg.get('total_reviews') or 0)
                else:
                    r['average_rating'] = None
                    r['total_reviews'] = 0
    except Exception:
        pass

    cursor.close()
    db.close()
    return jsonify(results)

# Get nearby places (simple version: within latitude/longitude range)
@api_bp.route('/nearby')
def nearby_places():
    # radius is expected in kilometers. We'll compute a bounding box to limit
    # the DB query and then filter precisely using the haversine formula.
    try:
        lat = float(request.args.get('lat', None))
        lng = float(request.args.get('lng', None))
    except (TypeError, ValueError):
        return jsonify({'error': 'lat and lng query parameters are required and must be numbers'}), 400

    try:
        radius_km = float(request.args.get('radius', 0.1))
    except (TypeError, ValueError):
        radius_km = 0.1

    # approximate degrees per km at given latitude
    # 1 degree latitude ~= 111.32 km
    deg_lat = radius_km / 111.32
    # 1 degree longitude ~= 111.32 * cos(lat) km
    lat_rad = math.radians(lat)
    deg_lng = radius_km / (111.32 * max(0.000001, math.cos(lat_rad)))

    min_lat = lat - deg_lat
    max_lat = lat + deg_lat
    min_lng = lng - deg_lng
    max_lng = lng + deg_lng

    db = get_db()
    cursor = db.cursor(dictionary=True)
    # Select candidates within bounding box to reduce work
    try:
        cursor.execute(
            "SELECT * FROM places WHERE latitude BETWEEN %s AND %s AND longitude BETWEEN %s AND %s",
            (min_lat, max_lat, min_lng, max_lng),
        )
    except Exception:
        # Fallback in case the table or columns have different names
        cursor.execute("SELECT * FROM places")

    candidates = cursor.fetchall()
    cursor.close()
    db.close()

    # Haversine filter to compute great-circle distance in km
    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    results = []
    for p in candidates:
        try:
            plat = float(p.get('latitude') or p.get('lat') or 0)
            plng = float(p.get('longitude') or p.get('lng') or 0)
        except Exception:
            continue
        dist = haversine_km(lat, lng, plat, plng)
        if dist <= radius_km:
            # attach distance if useful
            p['_distance_km'] = round(dist, 3)
            results.append(p)

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

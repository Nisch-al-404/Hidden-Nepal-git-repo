
from . import viewer_bp
from flask import render_template, abort
from app.models import get_db

@viewer_bp.route('/')
def homepage():
   return render_template("index.html")

@viewer_bp.route('/places')
def places_list():
   db = get_db()
   cursor = db.cursor(dictionary=True)
   cursor.execute("SELECT * FROM places ORDER BY created_at DESC")
   places = cursor.fetchall()
   cursor.close()
   db.close()
   return render_template("places_list.html", places=places)

@viewer_bp.route('/places/<int:place_id>')
def place_detail(place_id):
   db = get_db()
   cursor = db.cursor(dictionary=True)
   cursor.execute("SELECT * FROM places WHERE id = %s", (place_id,))
   place = cursor.fetchone()
   cursor.close()
   db.close()
   if not place:
      abort(404)
   return render_template("place_detail.html", place=place)

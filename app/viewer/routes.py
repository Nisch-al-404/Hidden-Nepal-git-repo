from flask import render_template, abort, request
from app.models import get_db
from . import viewer_bp

@viewer_bp.route('/about')
def about():
   return render_template("about.html")

@viewer_bp.route('/contact')
def contact():
   return render_template("contact.html")

@viewer_bp.route('/faq')
def faq():
   return render_template("faq.html")

@viewer_bp.route('/')
def homepage():
   return render_template("index.html")

@viewer_bp.route('/places')
def places_list():
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
   cursor.close()
   db.close()
   return render_template("places_list.html", places=places)

@viewer_bp.route('/places/<int:place_id>')
def place_detail(place_id):
   db = get_db()
   cursor = db.cursor(dictionary=True)
   cursor.execute("SELECT * FROM Places WHERE id = %s", (place_id,))
   place = cursor.fetchone()
   cursor.close()
   db.close()
   if not place:
      abort(404)
   return render_template("place_detail.html", place=place)

@viewer_bp.route('/dbtest')
def dbtest():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        db.close()
        return "Database connection successful!"
    except Exception as e:
        return f"Database connection failed: {e}"

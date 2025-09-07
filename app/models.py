import mysql.connector
from flask_login import UserMixin


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",               # Default XAMPP user
        password="pawan1321",            # Default: empty (no password)
        database="hidden_nepal"    # Your database name in phpMyAdmin
    )

class User(UserMixin):
    def __init__(self, id,name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role



# Image model and fetch function
class Image:
    def __init__(self, id, image_url, description, weather, temperature):
        self.id = id
        self.image_url = image_url
        self.description = description
        self.weather = weather
        self.temperature = temperature

def get_images():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, image_url, description, weather, temperature FROM images")
    images = [Image(**row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return images
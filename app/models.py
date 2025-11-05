
from flask_login import UserMixin

from flask import g
import mysql.connector
from mysql.connector import Error

def get_db():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host="127.0.0.1",
                port=3306,
                user="root",
                password="Pawan23@316#",
                database="hidden_nepal"
            )
            print("✅ Database connection established")
        except Error as e:
            print("❌ Database connection failed:", e)
            g.db = None
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        print("Database connection closed")







class User(UserMixin):
    def __init__(self, user_id,name, email, role):
      
        self.id = user_id
    def __init__(self, user_id,name, email, role):
      
        self.id = user_id
        self.name = name
        self.email = email
        self.role = role

# Add Place Model
class Place:
    def __init__(self, name, description, latitude, longitude, image_url, contributor_id, status, created_at):
       
        self.name = name
        self.description = description
        self.latitude = latitude
        self.longitude = longitude
        self.image_url = image_url
        self.contributor_id = contributor_id
        self.status = status
        self.created_at = created_at
    def save(self):
        db = get_db()
        cursor = db.cursor()
        query = """
        INSERT INTO Places (name, description, latitude, longitude, image_url, contributor_id, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (self.name, self.description, self.latitude, self.longitude, self.image_url, self.contributor_id, self.status, self.created_at))
        db.commit()
        cursor.close()
        db.close()
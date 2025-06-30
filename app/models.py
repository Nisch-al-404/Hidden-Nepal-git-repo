import mysql.connector
from flask_login import UserMixin


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",               # Default XAMPP user
        password="rOoT@12#3",               # Default: empty (no password)
        database="hiddennepal"    # Your database name in phpMyAdmin
    )



class User(UserMixin):
    def __init__(self, id,name, email, role):
      
        self.id = id
        self.name = name
        self.email = email
        self.role = role

#Add Place Model
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
        INSERT INTO places (name, description, latitude, longitude, image_url, contributor_id, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (self.name, self.description, self.latitude, self.longitude,
                               self.image_url, self.contributor_id, self.status, self.created_at))
        db.commit()
        cursor.close()
        db.close()    
# contribute1@gmail.com contribute1
import mysql.connector
from flask_login import UserMixin


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",               # Default XAMPP user
        password="",               # Default: empty (no password)
        database="hidden_nepal"    # Your database name in phpMyAdmin
    )

class User(UserMixin):
    def __init__(self, id,name, email, role):
        self.id = id
        self.name = name
        self.email = email
        self.role = role


# contribute1@gmail.com contribute1
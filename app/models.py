
from flask_login import UserMixin
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Load database config, or create a new one if not found."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return create_config_interactively()

def create_config_interactively():
    """Ask user for DB details and save them."""
    print("\n⚙️ Database configuration not found or invalid.")
    print("Please enter your MySQL database details:\n")

    host = input("Host (default: localhost): ") or "localhost"
    user = input("User (default: root): ") or "root"
    password = input("Password: ")
    database = input("Database name: ")

    config = {
        "mysql": {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
    }

    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

    print("\n✅ Configuration saved to config.json successfully!\n")
    return config

def get_db():
    """Establish a MySQL connection, ask for new details if error occurs."""
    config = load_config()

    try:
        db_config = config["mysql"]
        connection = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )

        if connection.is_connected():
            print("✅ Database connection successful!")
            return connection

    except mysql.connector.Error as err:
        print(f"\n❌ Database connection failed: {err}")
        print("Let's reconfigure your database connection.")
        config = create_config_interactively()
        return get_db()  # Try again recursively

# Example usage
if __name__ == "__main__":
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    print(cursor.fetchall())
    conn.close()






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
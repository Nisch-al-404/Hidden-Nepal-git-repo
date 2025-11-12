import mysql.connector
from mysql.connector import Error

def create_connection():
    """Establish a MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="root1234",  # MySQL user password
            database="Project2"
           
        )

       

        if connection.is_connected():
            print("✅ Database connection successful!")
            return connection

    except Error as e:
        print(f"❌ Error while connecting to MySQL: {e}")
        return None


def close_connection(connection):
    """Close MySQL database connection safely."""
    if connection and connection.is_connected():
        connection.close()
        print("🔒 Connection closed.")


if __name__ == "__main__":
    conn = create_connection()
    if conn:
        # You can run queries here later
        close_connection(conn)

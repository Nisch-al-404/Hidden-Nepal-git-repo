import mysql.connector
from mysql.connector import Error

print("🚀 Script started")

def create_connection():
    print("🔧 Inside create_connection()")
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="Pawan23@316#",  # whatever worked in CLI
            database="hidden_nepal",
            auth_plugin='mysql_native_password',
            connection_timeout=5
        )
        print("✅ mysql.connector.connect() called")

        if connection.is_connected():
            print("✅ Database connection successful!")
            return connection
        else:
            print("⚠️ Connection not established.")
            return None

    except Error as e:
        print(f"❌ Error while connecting to MySQL: {e}")
        return None

def close_connection(connection):
    print("🧹 Closing connection...")
    if connection and connection.is_connected():
        connection.close()
        print("🔒 Connection closed.")

if __name__ == "__main__":
    print("▶ Running main...")
    conn = create_connection()
    if conn:
        close_connection(conn)
    else:
        print("⚠️ Connection object is None")


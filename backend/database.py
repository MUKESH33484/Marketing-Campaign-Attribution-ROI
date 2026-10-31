import os
from pathlib import Path
import mysql.connector
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")


def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )

        if connection.is_connected():
            print("MySQL connected successfully!")
            return connection

    except mysql.connector.Error as error:
        print("Database connection failed:", error)

    return None


if __name__ == "__main__":
    connection = get_connection()

    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        print("Connected database:", cursor.fetchone()[0])

        cursor.close()
        connection.close()
        print("Connection closed.")

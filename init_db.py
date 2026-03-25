import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def init_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            sslmode="require"
        )
        cursor = conn.cursor()

        with open("database/schema.sql", "r") as f:
            sql = f.read()

        cursor.execute(sql)
        conn.commit()

        print("✓ Database initialized successfully")
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"✗ Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
    
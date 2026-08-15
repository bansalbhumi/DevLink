import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    conn.autocommit = True
    return conn

def init_db():
    if "DATABASE_URL" not in os.environ:
        print("DATABASE_URL not found. Skipping DB initialization.")
        return
        
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS urls (
                        id SERIAL PRIMARY KEY,
                        short_code TEXT UNIQUE NOT NULL,
                        original_url TEXT NOT NULL,
                        api_key TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS clicks (
                        id SERIAL PRIMARY KEY,
                        short_code TEXT NOT NULL,
                        ip_address TEXT,
                        clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)"
                )
    except Exception as e:
        # Ignore race conditions if Vercel boots up multiple instances at the exact same time
        print(f"DB init safely skipped a concurrent table creation race condition: {e}")
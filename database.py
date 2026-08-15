import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    # Fetch the connection string we will put in Vercel's Environment Variables
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set!")
    
    # Connects securely to Neon Postgres and returns rows as dictionaries
    conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    conn.autocommit = True
    return conn


# call this once on startup to set up tables
def init_db():
    if "DATABASE_URL" not in os.environ:
        print("DATABASE_URL not found. Skipping DB initialization.")
        return
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Postgres uses SERIAL instead of AUTOINCREMENT
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
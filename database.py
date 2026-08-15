# using sqlite for simplicity; would swap to postgres for real traffic
import sqlite3

DB_PATH = "devlink.db"


def get_connection():
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  conn.execute("PRAGMA journal_mode=WAL")  # better for concurrent reads
  return conn


# call this once on startup to set up tables
def init_db():
  with get_connection() as conn:
    conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT UNIQUE NOT NULL,
                original_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                short_code TEXT NOT NULL,
                ip_address TEXT,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)"
    )
    conn.commit()
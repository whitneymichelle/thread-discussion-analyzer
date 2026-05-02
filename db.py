import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/reddit_thread_agent.db")


def get_connection():
    """Return a SQLite connection, creating the data folder if needed."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create all tables for the project."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reddit_url TEXT UNIQUE NOT NULL,
        title TEXT,
        subreddit TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER NOT NULL,
        reddit_comment_id TEXT UNIQUE NOT NULL,
        body TEXT NOT NULL,
        score INTEGER,
        author TEXT,
        created_utc REAL,
        FOREIGN KEY (thread_id) REFERENCES threads(id)
    );

    CREATE TABLE IF NOT EXISTS mentions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comment_id INTEGER NOT NULL,
        entity_type TEXT NOT NULL,
        entity_name TEXT NOT NULL,
        sentiment TEXT,
        reason TEXT,
        FOREIGN KEY (comment_id) REFERENCES comments(id)
    );

    CREATE TABLE IF NOT EXISTS comment_embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        comment_id INTEGER UNIQUE NOT NULL,
        embedding TEXT NOT NULL,
        model TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (comment_id) REFERENCES comments(id)
    );

    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        entity_name TEXT NOT NULL,
        feedback_type TEXT NOT NULL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS answer_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        feedback_type TEXT NOT NULL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")

import os
import sqlite3

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/reddit_fandom.db")


def get_connection():
    """Return a SQLite connection, creating the data folder if needed."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def table_columns(cur, table_name: str) -> set[str]:
    """Return column names for a SQLite table."""
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def migrate_legacy_reddit_tables(cur):
    """
    Upgrade the first raw JSON import schema into the app schema.

    The original process_reddit.py created threads/comments without internal
    integer ids. The rest of the app needs those ids for mentions/embeddings.
    """
    thread_columns = table_columns(cur, "threads")
    comment_columns = table_columns(cur, "comments")

    if thread_columns and "id" not in thread_columns:
        cur.execute("ALTER TABLE threads RENAME TO threads_legacy")

    if comment_columns and "id" not in comment_columns:
        cur.execute("ALTER TABLE comments RENAME TO comments_legacy")


def init_db():
    """Create all tables for the project."""
    conn = get_connection()
    cur = conn.cursor()

    migrate_legacy_reddit_tables(cur)

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS threads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reddit_thread_id TEXT UNIQUE,
        title TEXT,
        body TEXT,
        author_hash TEXT,
        created_utc REAL,
        score INTEGER,
        upvote_ratio REAL,
        num_comments INTEGER,
        subreddit TEXT,
        permalink TEXT,
        url TEXT,
        source_file TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id INTEGER NOT NULL,
        reddit_comment_id TEXT UNIQUE,
        reddit_parent_id TEXT,
        author_hash TEXT,
        body TEXT,
        score INTEGER,
        created_utc REAL,
        depth INTEGER,
        subreddit TEXT,
        permalink TEXT,
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

    existing_tables = {
        row[0]
        for row in cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }

    if "threads_legacy" in existing_tables:
        cur.execute("""
            INSERT OR IGNORE INTO threads (
                reddit_thread_id, title, body, author_hash, created_utc, score,
                upvote_ratio, num_comments, subreddit, permalink, url, source_file
            )
            SELECT
                thread_id, title, body, author_hash, created_utc, score,
                upvote_ratio, num_comments, subreddit, permalink, url, source_file
            FROM threads_legacy
        """)

    if "comments_legacy" in existing_tables:
        cur.execute("""
            INSERT OR IGNORE INTO comments (
                thread_id, reddit_comment_id, reddit_parent_id, author_hash,
                body, created_utc, score, depth, subreddit, permalink
            )
            SELECT
                threads.id,
                comments_legacy.comment_id,
                comments_legacy.parent_id,
                comments_legacy.author_hash,
                comments_legacy.body,
                comments_legacy.created_utc,
                comments_legacy.score,
                comments_legacy.depth,
                comments_legacy.subreddit,
                comments_legacy.permalink
            FROM comments_legacy
            JOIN threads
              ON comments_legacy.thread_id = threads.reddit_thread_id
        """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")

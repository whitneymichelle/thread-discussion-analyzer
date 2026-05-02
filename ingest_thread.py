from db import get_connection, init_db
from reddit_client import get_reddit_client


def ingest_thread(thread_url: str):
    """Pull a Reddit submission and comments, then store them locally."""
    init_db()

    reddit = get_reddit_client()
    submission = reddit.submission(url=thread_url)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO threads (reddit_url, title, subreddit)
        VALUES (?, ?, ?)
    """, (thread_url, submission.title, str(submission.subreddit)))

    cur.execute("SELECT id FROM threads WHERE reddit_url = ?", (thread_url,))
    thread_id = cur.fetchone()[0]

    submission.comments.replace_more(limit=0)

    inserted = 0
    for comment in submission.comments.list():
        if not getattr(comment, "body", None):
            continue

        cur.execute("""
            INSERT OR IGNORE INTO comments
            (thread_id, reddit_comment_id, body, score, author, created_utc)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            thread_id,
            comment.id,
            comment.body,
            comment.score,
            str(comment.author) if comment.author else None,
            comment.created_utc,
        ))

        inserted += cur.rowcount

    conn.commit()
    conn.close()

    print(f"Ingested thread: {submission.title}")
    print(f"New comments inserted: {inserted}")


if __name__ == "__main__":
    url = input("Paste Reddit thread URL: ").strip()
    ingest_thread(url)

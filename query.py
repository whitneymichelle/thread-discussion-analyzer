from db import get_connection, init_db


def get_top_books(limit: int = 10):
    """Return most-mentioned positively/mixed books."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            entity_name,
            COUNT(*) AS mention_count,
            AVG(comments.score) AS avg_score
        FROM mentions
        JOIN comments ON mentions.comment_id = comments.id
        WHERE entity_type = 'book'
          AND sentiment IN ('positive', 'mixed')
        GROUP BY entity_name
        ORDER BY mention_count DESC, avg_score DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_top_topics(limit: int = 10):
    """Return most-mentioned topics."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT entity_name, COUNT(*) AS mention_count
        FROM mentions
        WHERE entity_type = 'topic'
        GROUP BY entity_name
        ORDER BY mention_count DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_reasons_for_book(book_name: str, limit: int = 10):
    """Return extracted reasons and source comments for a specific book."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT mentions.reason, comments.body, comments.score
        FROM mentions
        JOIN comments ON mentions.comment_id = comments.id
        WHERE LOWER(entity_name) = LOWER(?)
        ORDER BY comments.score DESC
        LIMIT ?
    """, (book_name, limit))

    rows = cur.fetchall()
    conn.close()
    return rows

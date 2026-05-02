from db import get_connection, init_db


def save_feedback(user_id: str, entity_name: str, feedback_type: str, note: str = ""):
    """
    Store personal preference feedback.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_feedback
        (user_id, entity_name, feedback_type, note)
        VALUES (?, ?, ?, ?)
    """, (user_id, entity_name, feedback_type, note))

    conn.commit()
    conn.close()


def save_answer_feedback(question: str, answer: str, feedback_type: str, note: str = ""):
    """
    Store answer quality feedback for later system improvement.

    This does not automatically retrain the model.
    """
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO answer_feedback
        (question, answer, feedback_type, note)
        VALUES (?, ?, ?, ?)
    """, (question, answer, feedback_type, note))

    conn.commit()
    conn.close()


def get_feedback_summary(user_id: str):
    """Return all personal feedback for a user."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT feedback_type, entity_name, note, created_at
        FROM user_feedback
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_positive_preferences(user_id: str):
    """Return entities the user liked or saved."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT entity_name, COUNT(*) AS feedback_count
        FROM user_feedback
        WHERE user_id = ?
          AND feedback_type IN ('liked', 'saved')
        GROUP BY entity_name
        ORDER BY feedback_count DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_negative_preferences(user_id: str):
    """Return entities the user disliked or rejected."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT entity_name, COUNT(*) AS feedback_count
        FROM user_feedback
        WHERE user_id = ?
          AND feedback_type IN ('disliked', 'rejected')
        GROUP BY entity_name
        ORDER BY feedback_count DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_recent_answer_feedback(limit: int = 20):
    """Return recent answer feedback for manual review."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT question, answer, feedback_type, note, created_at
        FROM answer_feedback
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows

import json
from db import get_connection, init_db
from client_helper import get_openai_client


def extract_mentions_from_comment(comment_body: str) -> list[dict]:
    """
    Use an LLM to convert one Reddit comment into structured mentions.
    """
    prompt = f"""
Extract structured mentions from this Reddit comment.

Look for:
- books
- authors
- topics/themes

Return JSON only in this format:
[
  {{
    "entity_type": "book | author | topic",
    "entity_name": "name",
    "sentiment": "positive | negative | mixed | neutral",
    "reason": "short reason"
  }}
]

Rules:
- If there are no useful mentions, return [].
- Do not invent books, authors, or topics.
- Keep reasons short.

Comment:
{comment_body}
"""

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-5.5-mini",
        input=prompt,
    )

    text = response.output_text.strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        raise ValueError(f"OpenAI returned invalid JSON: {text[:500]}")


def process_unextracted_comments(limit: int = 25):
    """Find comments with no extracted mentions and process them."""
    init_db()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.body
        FROM comments c
        WHERE c.extracted_at IS NULL
          AND c.body IS NOT NULL
          AND TRIM(c.body) != ''
        LIMIT ?
    """, (limit,))

    comments = cur.fetchall()
    inserted = 0

    for comment_id, body in comments:
        mentions = extract_mentions_from_comment(body)

        for mention in mentions:
            entity_type = mention.get("entity_type")
            entity_name = mention.get("entity_name")

            if not entity_type or not entity_name:
                continue

            cur.execute("""
                INSERT INTO mentions
                (comment_id, entity_type, entity_name, sentiment, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (
                comment_id,
                entity_type,
                entity_name,
                mention.get("sentiment", "neutral"),
                mention.get("reason", ""),
            ))

            inserted += 1

        cur.execute(
            "UPDATE comments SET extracted_at = CURRENT_TIMESTAMP WHERE id = ?",
            (comment_id,),
        )

    conn.commit()
    conn.close()

    print(f"Processed {len(comments)} comments.")
    print(f"Inserted {inserted} mentions.")


if __name__ == "__main__":
    process_unextracted_comments()

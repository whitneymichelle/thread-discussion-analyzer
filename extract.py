import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from db import get_connection, init_db

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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

    response = client.responses.create(
        model="gpt-5.5-mini",
        input=prompt,
    )

    text = response.output_text.strip()

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def process_unextracted_comments(limit: int = 25):
    """Find comments with no extracted mentions and process them."""
    init_db()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.body
        FROM comments c
        LEFT JOIN mentions m ON c.id = m.comment_id
        WHERE m.id IS NULL
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

    conn.commit()
    conn.close()

    print(f"Processed {len(comments)} comments.")
    print(f"Inserted {inserted} mentions.")


if __name__ == "__main__":
    process_unextracted_comments()

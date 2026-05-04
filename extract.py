import json
from db import get_connection, init_db
from client_helper import get_openai_client


TOPIC_ALIASES = {
    "fanfic": "fanfiction",
    "fan fiction": "fanfiction",
    "fan-fiction": "fanfiction",
    "fandom writing": "fanfiction",
    "slash": "slash/MM fanfiction",
    "slash fiction": "slash/MM fanfiction",
    "slash fanfic": "slash/MM fanfiction",
    "slash fanfiction": "slash/MM fanfiction",
    "m/m fanfic": "slash/MM fanfiction",
    "m/m fanfiction": "slash/MM fanfiction",
    "mm fanfic": "slash/MM fanfiction",
    "mm fanfiction": "slash/MM fanfiction",
    "male/male fanfic": "slash/MM fanfiction",
    "male/male fanfiction": "slash/MM fanfiction",
    "male pairings": "slash/MM fanfiction",
    "fanfic of male pairings": "slash/MM fanfiction",
    "ship fic": "shipping",
    "shipping fic": "shipping",
    "character study": "characterization",
    "character studies": "characterization",
    "characterisation": "characterization",
}


def clean_json_response(text: str) -> str:
    """Remove Markdown code fences when the model wraps JSON in them."""
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def normalize_topic(topic: str) -> str:
    """Normalize common fandom topic variants without erasing useful subtopics."""
    normalized = " ".join(topic.strip().split())
    alias_key = normalized.lower()
    return TOPIC_ALIASES.get(alias_key, normalized)


def normalize_mention(mention: dict) -> dict:
    entity_type = mention.get("entity_type")

    if isinstance(entity_type, str) and entity_type.lower() == "topic":
        mention = mention.copy()
        mention["entity_type"] = "topic"
        mention["entity_name"] = normalize_topic(str(mention.get("entity_name", "")))

    return mention


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
- Normalize topics, but preserve meaningful fandom subcategories.
- Use "fanfiction" for general fanfic, fan fiction, or fandom writing.
- Use "slash/MM fanfiction" for slash fiction, M/M fanfic, male/male fanfic, or male pairings.
- Use "shipping" for ship fic or shipping.
- Use "characterization" for character study, characterization, or characterisation.

Comment:
{comment_body}
"""

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    text = clean_json_response(response.output_text)

    try:
        parsed = json.loads(text)
        return [normalize_mention(mention) for mention in parsed] if isinstance(parsed, list) else []
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

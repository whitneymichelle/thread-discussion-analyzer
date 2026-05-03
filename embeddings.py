import json
from typing import List, Tuple

from db import get_connection, init_db
from client_helper import get_openai_client

EMBEDDING_MODEL = "text-embedding-3-small"


def create_embedding(text: str) -> List[float]:
    """Turn text into a vector embedding."""
    client = get_openai_client()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def embed_unembedded_comments(limit: int = 50):
    """
    Create embeddings for comments that do not have them yet.

    This stores vectors as JSON text in SQLite for learning simplicity.
    """
    init_db()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.id, c.body
        FROM comments c
        LEFT JOIN comment_embeddings e ON c.id = e.comment_id
        WHERE e.id IS NULL
          AND c.body IS NOT NULL
          AND TRIM(c.body) != ''
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    inserted = 0

    for comment_id, body in rows:
        embedding = create_embedding(body)

        cur.execute("""
            INSERT OR IGNORE INTO comment_embeddings
            (comment_id, embedding, model)
            VALUES (?, ?, ?)
        """, (
            comment_id,
            json.dumps(embedding),
            EMBEDDING_MODEL
        ))

        inserted += cur.rowcount

    conn.commit()
    conn.close()

    print(f"Embedded {inserted} comments.")


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def semantic_search_comments(query: str, limit: int = 5) -> List[Tuple[float, str, int]]:
    """
    Search comments by meaning.

    This educational version scans all embeddings in Python.
    A production version would use pgvector or a vector database.
    """
    query_embedding = create_embedding(query)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.body, c.score, e.embedding
        FROM comment_embeddings e
        JOIN comments c ON e.comment_id = c.id
    """)

    results = []

    for body, score, embedding_json in cur.fetchall():
        stored_embedding = json.loads(embedding_json)
        similarity = cosine_similarity(query_embedding, stored_embedding)
        results.append((similarity, body, score or 0))

    conn.close()

    results.sort(reverse=True, key=lambda x: x[0])
    return results[:limit]


if __name__ == "__main__":
    embed_unembedded_comments()

    query = input("Semantic search query: ").strip()
    matches = semantic_search_comments(query)

    for similarity, body, score in matches:
        print("\\n---")
        print(f"Similarity: {similarity:.3f}")
        print(f"Score: {score}")
        print(body[:500])

from embeddings import semantic_search_comments
from feedback import get_positive_preferences, get_negative_preferences
from client_helper import get_openai_client


def answer_question_with_retrieval(question: str, user_id: str = "demo_user", limit: int = 6) -> str:
    """
    Simplest RAG flow:
    1. Search comments by semantic meaning.
    2. Add retrieved comments to the prompt.
    3. Ask the LLM to answer only from that evidence.
    4. Include user feedback preferences as optional personalization context.
    """
    retrieved = semantic_search_comments(question, limit=limit)

    if not retrieved:
        return "No embedded comments found yet. Run option 6 first."

    likes = get_positive_preferences(user_id)
    dislikes = get_negative_preferences(user_id)

    evidence_blocks = []

    for idx, (similarity, body, score) in enumerate(retrieved, start=1):
        evidence_blocks.append(
            f"[Comment {idx} | similarity={similarity:.3f} | score={score}]\\n{body}"
        )

    evidence = "\\n\\n".join(evidence_blocks)

    preference_context = f"""
Known user likes/saves:
{likes}

Known user dislikes/rejections:
{dislikes}
"""

    prompt = f"""
You are a Reddit thread intelligence assistant.

Answer the user's question using ONLY the retrieved Reddit comments below.
If the comments do not contain enough evidence, say that the thread does not provide enough evidence.

User question:
{question}

User preference context:
{preference_context}

Retrieved Reddit comments:
{evidence}

Answer:
"""

    client = get_openai_client()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )

    return response.output_text


if __name__ == "__main__":
    question = input("Ask a question about the ingested Reddit comments: ").strip()
    print(answer_question_with_retrieval(question))

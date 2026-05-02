from db import init_db
from ingest_thread import ingest_thread
from extract import process_unextracted_comments
from embeddings import embed_unembedded_comments, semantic_search_comments
from query import get_top_books, get_top_topics, get_reasons_for_book
from feedback import (
    save_feedback,
    save_answer_feedback,
    get_feedback_summary,
    get_recent_answer_feedback,
)
from rag import answer_question_with_retrieval


def main():
    init_db()

    while True:
        print("\\nReddit Thread Intelligence Agent")
        print("1. Ingest Reddit thread")
        print("2. Extract mentions from comments")
        print("3. Show top books")
        print("4. Show top topics")
        print("5. Explain why people mention a book")
        print("6. Embed comments")
        print("7. Semantic search comments")
        print("8. Ask a RAG question")
        print("9. Save personal preference feedback")
        print("10. Show personal feedback summary")
        print("11. Show recent answer feedback")
        print("12. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            url = input("Reddit thread URL: ").strip()
            ingest_thread(url)

        elif choice == "2":
            limit = input("How many comments? Default 25: ").strip()
            process_unextracted_comments(int(limit) if limit else 25)

        elif choice == "3":
            for entity_name, mention_count, avg_score in get_top_books():
                print(f"{entity_name}: {mention_count} mentions, avg score {avg_score:.1f}")

        elif choice == "4":
            for entity_name, mention_count in get_top_topics():
                print(f"{entity_name}: {mention_count} mentions")

        elif choice == "5":
            book = input("Book name: ").strip()
            reasons = get_reasons_for_book(book)

            for reason, comment, score in reasons:
                print("\\n---")
                print(f"Score: {score}")
                print(f"Reason: {reason}")
                print(f"Comment: {comment[:500]}")

        elif choice == "6":
            limit = input("How many comments? Default 50: ").strip()
            embed_unembedded_comments(int(limit) if limit else 50)

        elif choice == "7":
            query = input("Search by meaning: ").strip()
            results = semantic_search_comments(query)

            for similarity, body, score in results:
                print("\\n---")
                print(f"Similarity: {similarity:.3f}")
                print(f"Score: {score}")
                print(body[:500])

        elif choice == "8":
            user_id = input("User ID default demo_user: ").strip() or "demo_user"
            question = input("Question: ").strip()

            answer = answer_question_with_retrieval(question, user_id=user_id)

            print("\\nAnswer:")
            print(answer)

            answer_feedback = input("\\nWas this answer helpful? (good/bad/unclear/skip): ").strip().lower()

            if answer_feedback in ["good", "bad", "unclear"]:
                note = input("Optional note about the answer: ").strip()
                save_answer_feedback(
                    question=question,
                    answer=answer,
                    feedback_type=answer_feedback,
                    note=note,
                )
                print("Answer feedback saved.")

            preference = input("\\nSave a personal preference from this answer? (yes/no): ").strip().lower()

            if preference == "yes":
                entity = input("Book/topic/preference name: ").strip()
                feedback_type = input("Feedback type liked/disliked/saved/rejected: ").strip().lower()
                note = input("Optional note: ").strip()

                save_feedback(
                    user_id=user_id,
                    entity_name=entity,
                    feedback_type=feedback_type,
                    note=note,
                )
                print("Personal preference saved.")

        elif choice == "9":
            user_id = input("User ID default demo_user: ").strip() or "demo_user"
            entity = input("Book/topic/preference name: ").strip()
            feedback_type = input("Feedback type liked/disliked/saved/rejected: ").strip().lower()
            note = input("Optional note: ").strip()

            save_feedback(
                user_id=user_id,
                entity_name=entity,
                feedback_type=feedback_type,
                note=note,
            )
            print("Personal preference saved.")

        elif choice == "10":
            user_id = input("User ID default demo_user: ").strip() or "demo_user"
            rows = get_feedback_summary(user_id)

            for feedback_type, entity_name, note, created_at in rows:
                print(f"{created_at} | {feedback_type} | {entity_name} | {note}")

        elif choice == "11":
            rows = get_recent_answer_feedback()

            for question, answer, feedback_type, note, created_at in rows:
                print("\\n---")
                print(f"{created_at} | {feedback_type}")
                print(f"Question: {question}")
                print(f"Note: {note}")
                print(f"Answer: {answer[:500]}")

        elif choice == "12":
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()

# File Guide

- db.py: Creates SQLite tables.
- reddit_client.py: Creates Reddit API client.
- ingest_thread.py: Pulls Reddit comments into SQLite.
- extract.py: Uses an LLM to create structured mentions.
- query.py: Uses SQL to answer structured questions.
- embeddings.py: Creates embeddings and performs semantic search.
- rag.py: Uses semantic search + LLM to answer questions.
- feedback.py: Stores personal and answer-level feedback.
- app.py: Command-line interface tying everything together.

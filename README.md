# Thread Intelligence Agent

A learning-focused side project for building a small RAG-style agent over Reddit threads.

## What this project does

This app can:
1. Process saved Reddit JSON files
2. Store comments in SQLite
3. Extract structured mentions from comments using an LLM
4. Create embeddings for semantic search
5. Answer open-ended questions using RAG
6. Store two kinds of feedback:
   - personal preference feedback
   - answer quality feedback

## Mental model

Saved Reddit JSON -> SQLite comments -> extraction -> mentions table -> embeddings -> semantic search -> RAG answer -> feedback

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python db.py
python process_reddit.py
python app.py
```

## Roadmap

Near-term direction:

- Add a simple chat interface over the Reddit data.
- Combine setup steps so processing, extraction, and embeddings can run automatically when needed.
- Add thumbs up/down answer feedback.
- Surface top books and top topics in a sidebar.
- Separate answer feedback from user preference feedback.

Longer-term ideas:

- Save which Reddit comments were used to create each chat answer, so answers can be audited, sourced, and improved from feedback.
- Use feedback to improve retrieval and personalization.

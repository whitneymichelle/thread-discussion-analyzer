# Reddit Thread Intelligence Agent

A learning-focused side project for building a small RAG-style agent over Reddit threads.

## What this project does

This app can:
1. Ingest a Reddit thread
2. Store comments in SQLite
3. Extract structured mentions from comments using an LLM
4. Create embeddings for semantic search
5. Answer open-ended questions using RAG
6. Store two kinds of feedback:
   - personal preference feedback
   - answer quality feedback

## Mental model

Reddit thread -> SQLite comments -> extraction -> mentions table -> embeddings -> semantic search -> RAG answer -> feedback

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python db.py
python app.py
```

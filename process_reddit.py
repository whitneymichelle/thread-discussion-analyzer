import json
import hashlib
from pathlib import Path

from db import get_connection, init_db


RAW_DIR = Path("data/raw")


def hash_author(author: str | None) -> str | None:
    if not author or author == "[deleted]":
        return None

    return hashlib.sha256(author.encode("utf-8")).hexdigest()[:12]


def parse_comment(comment_node: dict, thread_id: str) -> list[dict]:
    data = comment_node["data"]

    row = {
        "reddit_thread_id": thread_id,
        "reddit_comment_id": data.get("id"),
        "reddit_parent_id": data.get("parent_id"),
        "author_hash": hash_author(data.get("author")),
        "body": data.get("body"),
        "created_utc": data.get("created_utc"),
        "score": data.get("score"),
        "depth": data.get("depth"),
        "subreddit": data.get("subreddit"),
        "permalink": data.get("permalink"),
    }

    rows = [row]

    replies = data.get("replies")

    if isinstance(replies, dict):
        children = replies.get("data", {}).get("children", [])

        for child in children:
            if child.get("kind") == "t1":
                rows.extend(parse_comment(child, thread_id))

    return rows


def process_file(file_path: Path) -> tuple[dict, list[dict]]:
    with open(file_path, "r", encoding="utf-8") as f:
        reddit_json = json.load(f)

    post = reddit_json[0]["data"]["children"][0]["data"]
    thread_id = post.get("id")

    thread_row = {
        "reddit_thread_id": thread_id,
        "title": post.get("title"),
        "body": post.get("selftext"),
        "author_hash": hash_author(post.get("author")),
        "created_utc": post.get("created_utc"),
        "score": post.get("score"),
        "upvote_ratio": post.get("upvote_ratio"),
        "num_comments": post.get("num_comments"),
        "subreddit": post.get("subreddit"),
        "permalink": post.get("permalink"),
        "url": post.get("url"),
        "source_file": file_path.name,
    }

    comments = []

    comment_nodes = reddit_json[1]["data"]["children"]

    for node in comment_nodes:
        if node.get("kind") == "t1":
            comments.extend(parse_comment(node, thread_id))

    return thread_row, comments


def main() -> None:
    init_db()

    all_threads = []
    all_comments = []

    json_files = sorted(RAW_DIR.glob("*.json"))

    for file_path in json_files:
        thread_row, comments = process_file(file_path)

        all_threads.append(thread_row)
        all_comments.extend(comments)

    with get_connection() as conn:
        cur = conn.cursor()

        for thread in all_threads:
            cur.execute("""
                INSERT INTO threads (
                    reddit_thread_id, title, body, author_hash, created_utc, score,
                    upvote_ratio, num_comments, subreddit, permalink, url, source_file
                )
                VALUES (
                    :reddit_thread_id, :title, :body, :author_hash, :created_utc,
                    :score, :upvote_ratio, :num_comments, :subreddit, :permalink,
                    :url, :source_file
                )
                ON CONFLICT(reddit_thread_id) DO UPDATE SET
                    title = excluded.title,
                    body = excluded.body,
                    author_hash = excluded.author_hash,
                    created_utc = excluded.created_utc,
                    score = excluded.score,
                    upvote_ratio = excluded.upvote_ratio,
                    num_comments = excluded.num_comments,
                    subreddit = excluded.subreddit,
                    permalink = excluded.permalink,
                    url = excluded.url,
                    source_file = excluded.source_file
            """, thread)

        thread_ids = {
            reddit_thread_id: db_thread_id
            for db_thread_id, reddit_thread_id in cur.execute(
                "SELECT id, reddit_thread_id FROM threads WHERE reddit_thread_id IS NOT NULL"
            )
        }

        for comment in all_comments:
            db_thread_id = thread_ids.get(comment["reddit_thread_id"])

            if db_thread_id is None:
                continue

            cur.execute("""
                INSERT INTO comments (
                    thread_id, reddit_comment_id, reddit_parent_id, author_hash,
                    body, created_utc, score, depth, subreddit, permalink
                )
                VALUES (
                    :thread_id, :reddit_comment_id, :reddit_parent_id, :author_hash,
                    :body, :created_utc, :score, :depth, :subreddit, :permalink
                )
                ON CONFLICT(reddit_comment_id) DO UPDATE SET
                    thread_id = excluded.thread_id,
                    reddit_parent_id = excluded.reddit_parent_id,
                    author_hash = excluded.author_hash,
                    body = excluded.body,
                    created_utc = excluded.created_utc,
                    score = excluded.score,
                    depth = excluded.depth,
                    subreddit = excluded.subreddit,
                    permalink = excluded.permalink
            """, {
                "thread_id": db_thread_id,
                **comment,
            })

    print(f"Processed {len(all_threads)} threads")
    print(f"Processed {len(all_comments)} comments")
    print("Updated database")


if __name__ == "__main__":
    main()

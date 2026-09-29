"""
ticket_lookup.py

Tool: finds similar historical tickets. The incoming message is reduced to
keywords, candidates are fetched with ILIKE, and ranked by how many distinct
keywords they contain (the old version matched the *entire* message as one
substring, so it almost never found anything).

Requires: Postgres running, DATABASE_URL set, tickets table seeded.
"""
import os
import re

import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")

_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "have", "has", "was", "are",
    "our", "your", "you", "but", "not", "can", "cannot", "cant", "after", "before",
    "when", "then", "than", "into", "getting", "get", "got", "just", "been", "does",
    "did", "why", "how", "what", "please", "help", "need", "user", "customer", "team",
    "hi", "hello", "thanks", "thank", "issue", "problem",
}


def _keywords(query: str, max_terms: int = 8) -> list[str]:
    words = re.findall(r"[a-z0-9]+", query.lower())
    kws = [w for w in dict.fromkeys(words) if len(w) >= 3 and w not in _STOP]
    return kws[:max_terms]


def _rank(rows: list[tuple], kws: list[str], limit: int) -> list[dict]:
    """rows: (ticket_id, title, resolution, category, body). Needs >=2 keyword
    hits (or 1 if the query only has 1 keyword) so a single generic word can't match."""
    min_hits = 1 if len(kws) == 1 else 2
    scored = []
    for r in rows:
        text = f"{r[1] or ''} {r[4] or ''}".lower()
        score = sum(1 for k in kws if k in text)
        if score >= min_hits:
            scored.append((score, r))
    scored.sort(key=lambda s: s[0], reverse=True)
    return [
        {"ticket_id": r[0], "title": r[1], "resolution": r[2], "category": r[3]}
        for _, r in scored[:limit]
    ]


def ticket_lookup(query: str, limit: int = 3) -> list[dict]:
    """Search historical tickets for similar past issues."""
    kws = _keywords(query)
    if not kws:
        return []
    patterns = [f"%{k}%" for k in kws]
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), connect_timeout=5)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ticket_id, title, resolution, category, body
            FROM tickets
            WHERE title ILIKE ANY(%s) OR body ILIKE ANY(%s)
            LIMIT 50;
            """,
            (patterns, patterns),
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return _rank(rows, kws, limit)
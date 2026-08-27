"""Conversation persistence — Postgres CRUD for agent conversations.

Conversations are stored as a single JSONB ``messages`` array per row, which
maps directly onto the Anthropic messages format. A plain per-invocation
connection is used (no pool): in a serverless runtime you get one connection at
a time, so pooling buys nothing.
"""
import json
import os

import psycopg2
from psycopg2.extras import Json


def conn():
    """Open a Postgres connection using DATABASE_URL from the environment."""
    return psycopg2.connect(os.environ["DATABASE_URL"])


def create_conversation(db, messages: list) -> int:
    """Insert a new conversation row and return its auto-assigned ID."""
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO conversations (messages) VALUES (%s) RETURNING id",
            (Json(messages),),
        )
        row = cur.fetchone()
    db.commit()
    return row[0]


def load_conversation(db, conv_id: int) -> list | None:
    """Load the message history for a conversation, or None if not found."""
    with db.cursor() as cur:
        cur.execute("SELECT messages FROM conversations WHERE id = %s", (conv_id,))
        row = cur.fetchone()
    if not row:
        return None
    raw = row[0]
    return raw if isinstance(raw, list) else json.loads(raw)


def update_conversation(db, conv_id: int, messages: list):
    """Persist an updated message history after the tool loop completes."""
    with db.cursor() as cur:
        cur.execute(
            "UPDATE conversations SET messages = %s, updated_at = now() WHERE id = %s",
            (Json(messages), conv_id),
        )
    db.commit()

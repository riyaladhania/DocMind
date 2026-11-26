
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Store database in the DocMind project folder
DB_PATH = Path(__file__).resolve().parent / "docmind_history.db"


# Connect to database
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Create database tables
def init_db():
    with get_connection() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            )
        """)

        # Add suggestions column if it does not exist
        columns = [
            row[1] for row in conn.execute(
                "PRAGMA table_info(messages)"
            ).fetchall()
        ]

        if "suggestions" not in columns:
            conn.execute("""
                ALTER TABLE messages
                ADD COLUMN suggestions TEXT DEFAULT '[]'
            """)


# Create a new conversation
def create_chat(title="New Chat"):
    now = datetime.now().isoformat(timespec="seconds")

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO chats
               (title, created_at, updated_at)
               VALUES (?, ?, ?)""",
            (title, now, now)
        )

        return cursor.lastrowid


# Save a message with sources and suggestions
def save_message(
    chat_id,
    role,
    content,
    sources=None,
    suggestions=None
):
    now = datetime.now().isoformat(timespec="seconds")

    sources_json = json.dumps(sources or [])
    suggestions_json = json.dumps(suggestions or [])

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO messages
               (chat_id, role, content, sources, suggestions, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                chat_id,
                role,
                content,
                sources_json,
                suggestions_json,
                now
            )
        )

        # Update conversation title and last activity
        if role == "user":
            conn.execute(
                """UPDATE chats
                   SET title = CASE
                       WHEN title = 'New Chat' THEN ?
                       ELSE title
                   END,
                   updated_at = ?
                   WHERE id = ?""",
                (content[:40], now, chat_id)
            )
        else:
            conn.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ?",
                (now, chat_id)
            )


# Get conversations that contain messages

def get_chats():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT * FROM chats
            WHERE TRIM(title) != 'New Chat'
            AND EXISTS (
                SELECT 1 FROM messages
                WHERE messages.chat_id = chats.id
                AND messages.role = 'user'
            )
            ORDER BY updated_at DESC
        """).fetchall()

        return [dict(row) for row in rows]


# Get only the two most recent conversations
def get_recent_chats(limit=2):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT * FROM chats
            WHERE EXISTS (
                SELECT 1 FROM messages
                WHERE messages.chat_id = chats.id
            )
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


# Delete one conversation and its messages
def delete_chat(chat_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chats WHERE id = ?",
            (chat_id,)
        )


# Delete all conversation history
def delete_all_chats():
    with get_connection() as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM chats")


# Get messages from one conversation
def get_messages(chat_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """SELECT * FROM messages
               WHERE chat_id = ?
               ORDER BY id ASC""",
            (chat_id,)
        ).fetchall()

        messages = [dict(row) for row in rows]

        for message in messages:
            message["sources"] = json.loads(
                message["sources"] or "[]"
            )

            message["suggestions"] = json.loads(
                message["suggestions"] or "[]"
            )

        return messages
    
# Delete one conversation and its messages
def delete_chat(chat_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM messages WHERE chat_id = ?",
            (chat_id,)
        )
        conn.execute(
            "DELETE FROM chats WHERE id = ?",
            (chat_id,)
        )


# Delete all conversations and messages
def delete_all_chats():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM messages")
        conn.execute("DELETE FROM chats")


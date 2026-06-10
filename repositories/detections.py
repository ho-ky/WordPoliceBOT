from __future__ import annotations

from pathlib import Path
import sqlite3


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def add_detection(
    database_path: Path,
    *,
    guild_id: int,
    word_id: int,
    word: str,
    user_id: int,
    channel_id: int,
    message_id: int,
) -> None:
    with _connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO detections (
                guild_id,
                word_id,
                word,
                user_id,
                channel_id,
                message_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (guild_id, word_id, word, user_id, channel_id, message_id),
        )

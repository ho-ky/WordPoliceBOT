from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3

from repositories.text import normalize_text


@dataclass(frozen=True, slots=True)
class WatchWord:
    id: int
    guild_id: int
    word: str
    notify_enabled: bool
    created_by: int | None
    created_at: str
    updated_at: str


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _row_to_watch_word(row: sqlite3.Row) -> WatchWord:
    return WatchWord(
        id=row["id"],
        guild_id=row["guild_id"],
        word=row["word"],
        notify_enabled=bool(row["notify_enabled"]),
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _normalized_word(word: str) -> str:
    return normalize_text(word.strip())


def add_watch_word(
    database_path: Path,
    *,
    guild_id: int,
    word: str,
    notify_enabled: bool,
    created_by: int | None,
) -> WatchWord:
    normalized_word = word.strip()
    if not normalized_word:
        raise ValueError("word is required.")

    incoming_normalized_word = _normalized_word(normalized_word)

    with _connect(database_path) as connection:
        existing_words = connection.execute(
            """
            SELECT id, word
            FROM watch_words
            WHERE guild_id = ?
            """,
            (guild_id,),
        ).fetchall()
        for existing_word in existing_words:
            if _normalized_word(existing_word["word"]) == incoming_normalized_word:
                raise ValueError("同じ監視ワードはすでに登録されています。")

        cursor = connection.execute(
            """
            INSERT INTO watch_words (guild_id, word, notify_enabled, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (guild_id, normalized_word, int(notify_enabled), created_by),
        )
        row = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
        assert row is not None
        return _row_to_watch_word(row)


def list_watch_words(database_path: Path, *, guild_id: int) -> list[WatchWord]:
    with _connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = ?
            ORDER BY id ASC
            """,
            (guild_id,),
        ).fetchall()
        return [_row_to_watch_word(row) for row in rows]


def get_watch_word(
    database_path: Path,
    *,
    guild_id: int,
    word_id: int,
) -> WatchWord | None:
    with _connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = ? AND id = ?
            """,
            (guild_id, word_id),
        ).fetchone()
        return None if row is None else _row_to_watch_word(row)


def update_watch_word(
    database_path: Path,
    *,
    guild_id: int,
    word_id: int,
    word: str | None = None,
    notify_enabled: bool | None = None,
) -> WatchWord:
    updates: list[str] = []
    parameters: list[object] = []
    normalized_update_word = _normalized_word(word) if word is not None else None

    if word is not None:
        normalized_word = word.strip()
        if not normalized_word:
            raise ValueError("word is required.")

        with _connect(database_path) as connection:
            existing_words = connection.execute(
                """
                SELECT id, word
                FROM watch_words
                WHERE guild_id = ? AND id != ?
                """,
                (guild_id, word_id),
            ).fetchall()
            for existing_word in existing_words:
                if _normalized_word(existing_word["word"]) == normalized_update_word:
                    raise ValueError("同じ監視ワードはすでに登録されています。")

        updates.append("word = ?")
        parameters.append(normalized_word)

    if notify_enabled is not None:
        updates.append("notify_enabled = ?")
        parameters.append(int(notify_enabled))

    if not updates:
        raise ValueError("At least one field must be updated.")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    parameters.extend([guild_id, word_id])

    with _connect(database_path) as connection:
        cursor = connection.execute(
            f"""
            UPDATE watch_words
            SET {", ".join(updates)}
            WHERE guild_id = ? AND id = ?
            """,
            parameters,
        )
        if cursor.rowcount == 0:
            raise LookupError("watch word not found.")

        row = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = ? AND id = ?
            """,
            (guild_id, word_id),
        ).fetchone()
        assert row is not None
        return _row_to_watch_word(row)


def delete_watch_word(database_path: Path, *, guild_id: int, word_id: int) -> bool:
    with _connect(database_path) as connection:
        cursor = connection.execute(
            """
            DELETE FROM watch_words
            WHERE guild_id = ? AND id = ?
            """,
            (guild_id, word_id),
        )
        return cursor.rowcount > 0

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from database import connect as _connect
from repositories.text import normalize_text


@dataclass(frozen=True, slots=True)
class WatchWord:
    id: int
    guild_id: int
    word: str
    notify_enabled: bool
    created_by: int | None
    created_at: datetime
    updated_at: datetime


def _row_to_watch_word(row: dict[str, Any]) -> WatchWord:
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
    database_url: str,
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

    with _connect(database_url) as connection:
        existing_words = connection.execute(
            """
            SELECT id, word
            FROM watch_words
            WHERE guild_id = %s
            """,
            (guild_id,),
        ).fetchall()
        for existing_word in existing_words:
            if _normalized_word(existing_word["word"]) == incoming_normalized_word:
                raise ValueError("同じ監視ワードはすでに登録されています。")

        cursor = connection.execute(
            """
            INSERT INTO watch_words (guild_id, word, notify_enabled, created_by)
            VALUES (%s, %s, %s, %s)
            RETURNING id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            """,
            (guild_id, normalized_word, notify_enabled, created_by),
        )
        row = cursor.fetchone()
        assert row is not None
        return _row_to_watch_word(row)


def list_watch_words(database_url: str, *, guild_id: int) -> list[WatchWord]:
    with _connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = %s
            ORDER BY id ASC
            """,
            (guild_id,),
        ).fetchall()
        return [_row_to_watch_word(row) for row in rows]


def get_watch_word(
    database_url: str,
    *,
    guild_id: int,
    word_id: int,
) -> WatchWord | None:
    with _connect(database_url) as connection:
        row = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = %s AND id = %s
            """,
            (guild_id, word_id),
        ).fetchone()
        return None if row is None else _row_to_watch_word(row)


def get_watch_word_by_word(
    database_url: str,
    *,
    guild_id: int,
    word: str,
) -> WatchWord | None:
    normalized_word = _normalized_word(word)
    if not normalized_word:
        return None

    with _connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = %s
            ORDER BY id ASC
            """,
            (guild_id,),
        ).fetchall()

    for row in rows:
        if _normalized_word(row["word"]) == normalized_word:
            return _row_to_watch_word(row)
    return None


def update_watch_word(
    database_url: str,
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

        with _connect(database_url) as connection:
            existing_words = connection.execute(
                """
                SELECT id, word
                FROM watch_words
                WHERE guild_id = %s AND id != %s
                """,
                (guild_id, word_id),
            ).fetchall()
            for existing_word in existing_words:
                if _normalized_word(existing_word["word"]) == normalized_update_word:
                    raise ValueError("同じ監視ワードはすでに登録されています。")

        updates.append("word = %s")
        parameters.append(normalized_word)

    if notify_enabled is not None:
        updates.append("notify_enabled = %s")
        parameters.append(notify_enabled)

    if not updates:
        raise ValueError("At least one field must be updated.")

    updates.append("updated_at = CURRENT_TIMESTAMP")
    parameters.extend([guild_id, word_id])

    with _connect(database_url) as connection:
        cursor = connection.execute(
            f"""
            UPDATE watch_words
            SET {", ".join(updates)}
            WHERE guild_id = %s AND id = %s
            """,
            parameters,
        )
        if cursor.rowcount == 0:
            raise LookupError("watch word not found.")

        row = connection.execute(
            """
            SELECT id, guild_id, word, notify_enabled, created_by, created_at, updated_at
            FROM watch_words
            WHERE guild_id = %s AND id = %s
            """,
            (guild_id, word_id),
        ).fetchone()
        assert row is not None
        return _row_to_watch_word(row)


def delete_watch_word(database_url: str, *, guild_id: int, word_id: int) -> bool:
    with _connect(database_url) as connection:
        cursor = connection.execute(
            """
            DELETE FROM watch_words
            WHERE guild_id = %s AND id = %s
            """,
            (guild_id, word_id),
        )
        return cursor.rowcount > 0

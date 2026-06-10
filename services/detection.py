from __future__ import annotations

from pathlib import Path

from repositories.detections import add_detection
from repositories.text import normalize_text
from repositories.watch_words import WatchWord, list_watch_words


def detect_and_record_message(
    database_path: Path,
    *,
    guild_id: int,
    content: str,
    user_id: int,
    channel_id: int,
    message_id: int,
) -> list[WatchWord]:
    normalized_content = normalize_text(content)
    matched_words: list[WatchWord] = []

    for watch_word in list_watch_words(database_path, guild_id=guild_id):
        normalized_word = normalize_text(watch_word.word.strip())
        if not normalized_word:
            continue
        if normalized_word not in normalized_content:
            continue

        add_detection(
            database_path,
            guild_id=guild_id,
            word_id=watch_word.id,
            word=watch_word.word,
            user_id=user_id,
            channel_id=channel_id,
            message_id=message_id,
        )
        matched_words.append(watch_word)

    return matched_words

from __future__ import annotations


from repositories.detections import add_detection
from repositories.readings import infer_watch_word_reading, message_reading
from repositories.watch_words import WatchWord, list_watch_words


def detect_and_record_message(
    database_url: str,
    *,
    guild_id: int,
    content: str,
    user_id: int,
    channel_id: int,
    message_id: int,
) -> list[WatchWord]:
    words = list_watch_words(database_url, guild_id=guild_id)
    if not words:
        return []

    normalized_content = message_reading(content)
    matched_words: list[WatchWord] = []

    for watch_word in words:
        normalized_word = watch_word.reading or infer_watch_word_reading(watch_word.word)
        if not normalized_word:
            continue
        occurrence_count = normalized_content.count(normalized_word)
        if occurrence_count == 0:
            continue

        add_detection(
            database_url,
            guild_id=guild_id,
            word_id=watch_word.id,
            word=watch_word.word,
            user_id=user_id,
            channel_id=channel_id,
            message_id=message_id,
            occurrence_count=occurrence_count,
        )
        matched_words.append(watch_word)

    return matched_words

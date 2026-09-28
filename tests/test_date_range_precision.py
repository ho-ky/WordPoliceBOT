from __future__ import annotations

from database import connect
from repositories.watch_words import add_watch_word
from services.stats import get_word_detection_count


def test_jst_end_date_includes_fractional_second(db_url: str) -> None:
    word = add_watch_word(
        db_url, guild_id=1, word="word", notify_enabled=True, created_by=None
    )
    with connect(db_url) as connection:
        connection.execute(
            """
            INSERT INTO detections (
                guild_id, word_id, word, user_id, channel_id, message_id, detected_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (1, word.id, word.word, 2, 3, 4, "2026-06-01 14:59:59.999999+00"),
        )

    assert get_word_detection_count(
        db_url, guild_id=1, word_id=word.id,
        from_date="2026-06-01", to_date="2026-06-01",
    ) == 1

from __future__ import annotations

from database import connect

from repositories.text import normalize_text
from repositories.watch_words import add_watch_word, get_watch_word_by_word, delete_watch_word
from repositories.detections import add_detection, count_detections


def test_postgres_tables_have_rls(db_url: str) -> None:
    with connect(db_url) as connection:
        rows = connection.execute(
            """
            SELECT relname, relrowsecurity
            FROM pg_class
            WHERE oid IN (
                'public.guild_settings'::regclass,
                'public.watch_words'::regclass,
                'public.detections'::regclass
            )
            """
        ).fetchall()
    assert {row["relname"]: row["relrowsecurity"] for row in rows} == {
        "guild_settings": True,
        "watch_words": True,
        "detections": True,
    }


def test_deleting_word_cascades_to_detections(db_url: str) -> None:
    word = add_watch_word(
        db_url, guild_id=1, word="word", notify_enabled=True, created_by=None
    )
    add_detection(
        db_url, guild_id=1, word_id=word.id, word=word.word,
        user_id=2, channel_id=3, message_id=4,
    )
    assert delete_watch_word(db_url, guild_id=1, word_id=word.id)
    assert count_detections(db_url, guild_id=1, word_id=word.id) == 0


def test_add_watch_word_keeps_original_display_value(db_url: str) -> None:
    db_path = db_url

    input_word = "ＡＢＣabc　"
    created = add_watch_word(
        db_path, guild_id=1, word=input_word, notify_enabled=True, created_by=None
    )

    # Stored word should preserve the original trimmed display value (strip applied)
    assert created.word == input_word.strip()


def test_detection_normalization_is_applied() -> None:
    assert normalize_text("ＡＢＣabc") == "abcabc"


def test_get_watch_word_by_word_uses_normalized_value(db_url: str) -> None:
    db_path = db_url
    created = add_watch_word(
        db_path,
        guild_id=1,
        word="ＡＢＣ",
        notify_enabled=True,
        created_by=None,
    )

    found = get_watch_word_by_word(db_path, guild_id=1, word=" abc ")

    assert found is not None
    assert found.id == created.id


def test_get_watch_word_by_word_is_scoped_to_guild(db_url: str) -> None:
    db_path = db_url
    add_watch_word(
        db_path,
        guild_id=1,
        word="word",
        notify_enabled=True,
        created_by=None,
    )

    assert get_watch_word_by_word(db_path, guild_id=2, word="word") is None

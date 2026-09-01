from __future__ import annotations

from pathlib import Path

from database import initialize_database
from repositories.detections import count_detections
from repositories.watch_words import add_watch_word
from services.detection import detect_and_record_message


def test_detect_and_record_counts_repeated_word_occurrences(tmp_path: Path) -> None:
    db_path = tmp_path / "detection.db"
    initialize_database(db_path)
    word = add_watch_word(
        db_path,
        guild_id=1,
        word="word",
        notify_enabled=True,
        created_by=None,
    )

    matched_words = detect_and_record_message(
        db_path,
        guild_id=1,
        content="word word word",
        user_id=10,
        channel_id=20,
        message_id=30,
    )

    assert [matched.word for matched in matched_words] == ["word"]
    assert count_detections(db_path, guild_id=1, word_id=word.id) == 3


def test_detect_and_record_counts_each_word_independently(tmp_path: Path) -> None:
    db_path = tmp_path / "detection_multiple_words.db"
    initialize_database(db_path)
    first_word = add_watch_word(
        db_path,
        guild_id=1,
        word="word",
        notify_enabled=True,
        created_by=None,
    )
    second_word = add_watch_word(
        db_path,
        guild_id=1,
        word="example",
        notify_enabled=True,
        created_by=None,
    )

    matched_words = detect_and_record_message(
        db_path,
        guild_id=1,
        content="word example example",
        user_id=10,
        channel_id=20,
        message_id=30,
    )

    assert [matched.word for matched in matched_words] == ["word", "example"]
    assert count_detections(db_path, guild_id=1, word_id=first_word.id) == 1
    assert count_detections(db_path, guild_id=1, word_id=second_word.id) == 2


def test_detect_and_record_applies_normalization_before_counting(tmp_path: Path) -> None:
    db_path = tmp_path / "detection_normalized.db"
    initialize_database(db_path)
    word = add_watch_word(
        db_path,
        guild_id=1,
        word="abc",
        notify_enabled=True,
        created_by=None,
    )

    detect_and_record_message(
        db_path,
        guild_id=1,
        content="ＡＢＣ abc AbC",
        user_id=10,
        channel_id=20,
        message_id=30,
    )

    assert count_detections(db_path, guild_id=1, word_id=word.id) == 3


def test_detect_and_record_does_not_count_overlapping_occurrences(tmp_path: Path) -> None:
    db_path = tmp_path / "detection_overlap.db"
    initialize_database(db_path)
    word = add_watch_word(
        db_path,
        guild_id=1,
        word="aa",
        notify_enabled=True,
        created_by=None,
    )

    detect_and_record_message(
        db_path,
        guild_id=1,
        content="aaa",
        user_id=10,
        channel_id=20,
        message_id=30,
    )

    assert count_detections(db_path, guild_id=1, word_id=word.id) == 1


def test_detection_log_is_saved_even_when_notification_is_disabled(tmp_path: Path) -> None:
    db_path = tmp_path / "detection_disabled_notification.db"
    initialize_database(db_path)
    word = add_watch_word(
        db_path,
        guild_id=1,
        word="word",
        notify_enabled=False,
        created_by=None,
    )

    matched_words = detect_and_record_message(
        db_path,
        guild_id=1,
        content="word word",
        user_id=10,
        channel_id=20,
        message_id=30,
    )

    assert [matched.word for matched in matched_words] == ["word"]
    assert count_detections(db_path, guild_id=1, word_id=word.id) == 2

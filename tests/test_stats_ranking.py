from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database import initialize_database
from repositories.watch_words import add_watch_word
from services.stats import (
    DEFAULT_RANKING_LIMIT,
    MAX_RANKING_LIMIT,
    get_word_detection_count,
    get_word_detection_ranking,
    parse_detection_date_range,
    validate_ranking_limit,
)


def _seed_detection(
    db_path: Path,
    *,
    guild_id: int,
    word_id: int,
    word: str,
    user_id: int,
    detected_at: str,
) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO detections (
                guild_id,
                word_id,
                word,
                user_id,
                channel_id,
                message_id,
                detected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, word_id, word, user_id, 100, 200, detected_at),
        )


def _prepare_word(db_path: Path) -> int:
    created = add_watch_word(
        db_path,
        guild_id=1,
        word="sample",
        notify_enabled=True,
        created_by=None,
    )
    return created.id


def test_parse_detection_date_range_converts_jst_to_utc() -> None:
    date_range = parse_detection_date_range("2026-06-01", "2026-06-01")

    assert date_range.detected_at_from == "2026-05-31 15:00:00"
    assert date_range.detected_at_to == "2026-06-01 14:59:59"


def test_parse_detection_date_range_rejects_invalid_date() -> None:
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_detection_date_range("2026-06-31", None)


def test_validate_ranking_limit_rejects_over_max() -> None:
    with pytest.raises(ValueError, match=str(MAX_RANKING_LIMIT)):
        validate_ranking_limit(MAX_RANKING_LIMIT + 1)


def test_get_word_detection_count_uses_jst_boundaries(tmp_path: Path) -> None:
    db_path = tmp_path / "stats.db"
    initialize_database(db_path)
    word_id = _prepare_word(db_path)

    _seed_detection(
        db_path,
        guild_id=1,
        word_id=word_id,
        word="sample",
        user_id=10,
        detected_at="2026-05-31 14:59:59",
    )
    _seed_detection(
        db_path,
        guild_id=1,
        word_id=word_id,
        word="sample",
        user_id=10,
        detected_at="2026-05-31 15:00:00",
    )
    _seed_detection(
        db_path,
        guild_id=1,
        word_id=word_id,
        word="sample",
        user_id=10,
        detected_at="2026-06-01 14:59:59",
    )
    _seed_detection(
        db_path,
        guild_id=1,
        word_id=word_id,
        word="sample",
        user_id=10,
        detected_at="2026-06-01 15:00:00",
    )

    assert get_word_detection_count(
        db_path,
        guild_id=1,
        word_id=word_id,
        from_date=None,
        to_date=None,
    ) == 4

    assert get_word_detection_count(
        db_path,
        guild_id=1,
        word_id=word_id,
        from_date="2026-06-01",
        to_date="2026-06-01",
    ) == 2


def test_get_word_detection_count_accepts_open_ended_range(tmp_path: Path) -> None:
    db_path = tmp_path / "stats_open.db"
    initialize_database(db_path)
    word_id = _prepare_word(db_path)

    _seed_detection(
        db_path,
        guild_id=1,
        word_id=word_id,
        word="sample",
        user_id=10,
        detected_at="2026-05-31 14:59:59",
    )
    _seed_detection(
        db_path,
        guild_id=1,
        word_id=word_id,
        word="sample",
        user_id=10,
        detected_at="2026-06-01 15:00:00",
    )

    assert get_word_detection_count(
        db_path,
        guild_id=1,
        word_id=word_id,
        from_date=None,
        to_date="2026-05-31",
    ) == 1


def test_get_word_detection_ranking_uses_default_limit(tmp_path: Path) -> None:
    db_path = tmp_path / "ranking_default.db"
    initialize_database(db_path)
    word_id = _prepare_word(db_path)

    for user_id in range(1, 12):
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=word_id,
            word="sample",
            user_id=user_id,
            detected_at="2026-06-01 00:00:00",
        )

    rows = get_word_detection_ranking(db_path, guild_id=1, word_id=word_id)

    assert len(rows) == DEFAULT_RANKING_LIMIT
    assert rows[0].count == 1


def test_get_word_detection_ranking_orders_by_count_and_user(tmp_path: Path) -> None:
    db_path = tmp_path / "ranking_order.db"
    initialize_database(db_path)
    word_id = _prepare_word(db_path)

    for _ in range(3):
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=word_id,
            word="sample",
            user_id=20,
            detected_at="2026-06-01 00:00:00",
        )
    for _ in range(2):
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=word_id,
            word="sample",
            user_id=10,
            detected_at="2026-06-01 00:00:00",
        )
    for _ in range(2):
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=word_id,
            word="sample",
            user_id=15,
            detected_at="2026-06-01 00:00:00",
        )

    rows = get_word_detection_ranking(
        db_path,
        guild_id=1,
        word_id=word_id,
        limit=3,
    )

    assert [row.user_id for row in rows] == [20, 10, 15]
    assert [row.count for row in rows] == [3, 2, 2]


def test_get_word_detection_ranking_rejects_limit_over_max() -> None:
    with pytest.raises(ValueError, match=str(MAX_RANKING_LIMIT)):
        validate_ranking_limit(MAX_RANKING_LIMIT + 1)

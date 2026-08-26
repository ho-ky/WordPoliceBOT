from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database import initialize_database
from commands.word import _competition_ranks, _format_ranking_line, _format_word_ranking_lines
from repositories.detections import DetectionRankingRow, WordDetectionRankingRow
from repositories.watch_words import add_watch_word
from services.stats import (
    DEFAULT_RANKING_LIMIT,
    MAX_RANKING_LIMIT,
    get_word_detection_count,
    get_detection_word_ranking,
    get_word_detection_ranking,
    parse_detection_date_range,
    validate_ranking_options,
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


def test_validate_ranking_options_collects_date_and_limit_errors() -> None:
    validated_limit, errors = validate_ranking_options(
        from_date="2026-06-31",
        to_date=None,
        limit=MAX_RANKING_LIMIT + 1,
    )

    assert validated_limit is None
    assert errors == [
        "日付は YYYY-MM-DD 形式で指定してください。",
        f"limit は {MAX_RANKING_LIMIT} 以下で指定してください。",
    ]


def test_validate_ranking_options_collects_only_date_error() -> None:
    validated_limit, errors = validate_ranking_options(
        from_date="invalid",
        to_date=None,
        limit=10,
    )

    assert validated_limit == 10
    assert errors == ["日付は YYYY-MM-DD 形式で指定してください。"]


def test_validate_ranking_options_collects_only_limit_error() -> None:
    validated_limit, errors = validate_ranking_options(
        from_date="2026-06-01",
        to_date="2026-06-30",
        limit=0,
    )

    assert validated_limit is None
    assert errors == ["limit は 1 以上で指定してください。"]


def test_validate_ranking_options_accepts_valid_input() -> None:
    validated_limit, errors = validate_ranking_options(
        from_date="2026-06-01",
        to_date="2026-06-30",
        limit=10,
    )

    assert validated_limit == 10
    assert errors == []


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


def test_get_detection_word_ranking_orders_by_count_and_word_id(tmp_path: Path) -> None:
    db_path = tmp_path / "word_ranking.db"
    initialize_database(db_path)
    first_word_id = _prepare_word(db_path)
    second_word = add_watch_word(
        db_path,
        guild_id=1,
        word="second",
        notify_enabled=True,
        created_by=None,
    )
    third_word = add_watch_word(
        db_path,
        guild_id=1,
        word="third",
        notify_enabled=True,
        created_by=None,
    )

    for _ in range(3):
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=first_word_id,
            word="sample",
            user_id=10,
            detected_at="2026-06-01 00:00:00",
        )
    for _ in range(2):
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=second_word.id,
            word="second",
            user_id=10,
            detected_at="2026-06-01 00:00:00",
        )
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=third_word.id,
            word="third",
            user_id=10,
            detected_at="2026-06-01 00:00:00",
        )

    rows = get_detection_word_ranking(db_path, guild_id=1, limit=3)

    assert [(row.word_id, row.word, row.count) for row in rows] == [
        (first_word_id, "sample", 3),
        (second_word.id, "second", 2),
        (third_word.id, "third", 2),
    ]


def test_get_detection_word_ranking_uses_jst_period_and_excludes_zero_count_words(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "word_ranking_period.db"
    initialize_database(db_path)
    word_id = _prepare_word(db_path)
    add_watch_word(
        db_path,
        guild_id=1,
        word="unused",
        notify_enabled=True,
        created_by=None,
    )

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

    rows = get_detection_word_ranking(
        db_path,
        guild_id=1,
        from_date="2026-06-01",
        to_date="2026-06-01",
    )

    assert [(row.word, row.count) for row in rows] == [("sample", 2)]


def test_get_detection_word_ranking_uses_default_and_custom_limit(tmp_path: Path) -> None:
    db_path = tmp_path / "word_ranking_limit.db"
    initialize_database(db_path)
    for index in range(DEFAULT_RANKING_LIMIT + 1):
        word = add_watch_word(
            db_path,
            guild_id=1,
            word=f"word-{index}",
            notify_enabled=True,
            created_by=None,
        )
        _seed_detection(
            db_path,
            guild_id=1,
            word_id=word.id,
            word=word.word,
            user_id=10,
            detected_at="2026-06-01 00:00:00",
        )

    assert len(get_detection_word_ranking(db_path, guild_id=1)) == DEFAULT_RANKING_LIMIT
    assert len(get_detection_word_ranking(db_path, guild_id=1, limit=3)) == 3


def test_format_word_ranking_lines_assigns_same_rank_to_tied_counts() -> None:
    rows = [
        WordDetectionRankingRow(word_id=1, word="first", count=5),
        WordDetectionRankingRow(word_id=2, word="second", count=3),
        WordDetectionRankingRow(word_id=3, word="third", count=3),
        WordDetectionRankingRow(word_id=4, word="fourth", count=1),
    ]

    assert _format_word_ranking_lines(rows) == [
        "1. `first` 5回",
        "2. `second` 3回",
        "2. `third` 3回",
        "4. `fourth` 1回",
    ]


def test_format_user_ranking_lines_assigns_same_rank_to_tied_counts() -> None:
    rows = [
        DetectionRankingRow(user_id=1, count=5),
        DetectionRankingRow(user_id=2, count=3),
        DetectionRankingRow(user_id=3, count=3),
        DetectionRankingRow(user_id=4, count=1),
    ]

    assert _competition_ranks([row.count for row in rows]) == [1, 2, 2, 4]
    assert [
        _format_ranking_line(rank, row)
        for rank, row in zip(_competition_ranks([row.count for row in rows]), rows)
    ] == [
        "1. <@1> 5回",
        "2. <@2> 3回",
        "2. <@3> 3回",
        "4. <@4> 1回",
    ]

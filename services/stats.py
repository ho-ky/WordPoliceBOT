from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from repositories.detections import (
    DetectionRankingRow,
    WordDetectionRankingRow,
    count_detections,
    get_detection_ranking,
    get_word_detection_ranking as fetch_word_detection_ranking,
)
from repositories.watch_words import WatchWord, get_watch_word


JST = timezone(timedelta(hours=9))
UTC = timezone.utc
DEFAULT_RANKING_LIMIT = 10
MAX_RANKING_LIMIT = 100


@dataclass(frozen=True, slots=True)
class UTCDateRange:
    detected_at_from: str | None
    detected_at_to: str | None


def _format_utc_sqlite(dt: datetime) -> str:
    return dt.astimezone(UTC).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S")


def _parse_jst_date(value: str, *, end_of_day: bool) -> str:
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("日付は YYYY-MM-DD 形式で指定してください。") from exc

    jst_time = time(23, 59, 59) if end_of_day else time(0, 0, 0)
    dt = datetime.combine(parsed_date, jst_time, tzinfo=JST)
    return _format_utc_sqlite(dt)


def parse_detection_date_range(
    from_date: str | None,
    to_date: str | None,
) -> UTCDateRange:
    detected_at_from = _parse_jst_date(from_date, end_of_day=False) if from_date else None
    detected_at_to = _parse_jst_date(to_date, end_of_day=True) if to_date else None
    return UTCDateRange(detected_at_from=detected_at_from, detected_at_to=detected_at_to)


def validate_ranking_limit(limit: int) -> int:
    if limit <= 0:
        raise ValueError("limit は 1 以上で指定してください。")
    if limit > MAX_RANKING_LIMIT:
        raise ValueError(f"limit は {MAX_RANKING_LIMIT} 以下で指定してください。")
    return limit


def validate_ranking_options(
    *,
    from_date: str | None,
    to_date: str | None,
    limit: int,
) -> tuple[int | None, list[str]]:
    errors: list[str] = []
    validated_limit: int | None = None

    try:
        parse_detection_date_range(from_date, to_date)
    except ValueError as exc:
        errors.append(str(exc))

    try:
        validated_limit = validate_ranking_limit(limit)
    except ValueError as exc:
        errors.append(str(exc))

    return validated_limit, errors


def get_watch_word_or_raise(database_path: Path, *, guild_id: int, word_id: int) -> WatchWord:
    watch_word = get_watch_word(database_path, guild_id=guild_id, word_id=word_id)
    if watch_word is None:
        raise LookupError("指定した監視ワードが見つかりません。")
    return watch_word


def get_word_detection_count(
    database_path: Path,
    *,
    guild_id: int,
    word_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
) -> int:
    date_range = parse_detection_date_range(from_date, to_date)
    return count_detections(
        database_path,
        guild_id=guild_id,
        word_id=word_id,
        detected_at_from=date_range.detected_at_from,
        detected_at_to=date_range.detected_at_to,
    )


def get_word_detection_ranking(
    database_path: Path,
    *,
    guild_id: int,
    word_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
) -> list[DetectionRankingRow]:
    validated_limit = validate_ranking_limit(limit)
    date_range = parse_detection_date_range(from_date, to_date)
    return get_detection_ranking(
        database_path,
        guild_id=guild_id,
        word_id=word_id,
        detected_at_from=date_range.detected_at_from,
        detected_at_to=date_range.detected_at_to,
        limit=validated_limit,
    )


def get_detection_word_ranking(
    database_path: Path,
    *,
    guild_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
) -> list[WordDetectionRankingRow]:
    validated_limit = validate_ranking_limit(limit)
    date_range = parse_detection_date_range(from_date, to_date)
    return fetch_word_detection_ranking(
        database_path,
        guild_id=guild_id,
        detected_at_from=date_range.detected_at_from,
        detected_at_to=date_range.detected_at_to,
        limit=validated_limit,
    )

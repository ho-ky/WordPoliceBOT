from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

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
    detected_at_from: datetime | None
    detected_at_to: datetime | None


def competition_ranks(counts: Iterable[int]) -> list[int]:
    """Return competition ranks for counts already ordered from highest to lowest."""
    ranks: list[int] = []
    previous_count: int | None = None
    rank = 0

    for index, count in enumerate(counts, start=1):
        if count != previous_count:
            rank = index
            previous_count = count
        ranks.append(rank)

    return ranks


def _parse_jst_date(value: str, *, next_day: bool) -> datetime:
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("日付は YYYY-MM-DD 形式で指定してください。") from exc

    if next_day:
        parsed_date += timedelta(days=1)
    return datetime.combine(parsed_date, time.min, tzinfo=JST).astimezone(UTC)


def parse_detection_date_range(
    from_date: str | None,
    to_date: str | None,
) -> UTCDateRange:
    detected_at_from = _parse_jst_date(from_date, next_day=False) if from_date else None
    detected_at_to = _parse_jst_date(to_date, next_day=True) if to_date else None
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


def get_watch_word_or_raise(database_url: str, *, guild_id: int, word_id: int) -> WatchWord:
    watch_word = get_watch_word(database_url, guild_id=guild_id, word_id=word_id)
    if watch_word is None:
        raise LookupError("指定した監視ワードが見つかりません。")
    return watch_word


def get_word_detection_count(
    database_url: str,
    *,
    guild_id: int,
    word_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
) -> int:
    date_range = parse_detection_date_range(from_date, to_date)
    return count_detections(
        database_url,
        guild_id=guild_id,
        word_id=word_id,
        detected_at_from=date_range.detected_at_from,
        detected_at_to=date_range.detected_at_to,
    )


def get_word_detection_ranking(
    database_url: str,
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
        database_url,
        guild_id=guild_id,
        word_id=word_id,
        detected_at_from=date_range.detected_at_from,
        detected_at_to=date_range.detected_at_to,
        limit=validated_limit,
    )


def get_detection_word_ranking(
    database_url: str,
    *,
    guild_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
) -> list[WordDetectionRankingRow]:
    validated_limit = validate_ranking_limit(limit)
    date_range = parse_detection_date_range(from_date, to_date)
    return fetch_word_detection_ranking(
        database_url,
        guild_id=guild_id,
        detected_at_from=date_range.detected_at_from,
        detected_at_to=date_range.detected_at_to,
        limit=validated_limit,
    )

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from database import connect as _connect


@dataclass(frozen=True, slots=True)
class DetectionRankingRow:
    user_id: int
    count: int


@dataclass(frozen=True, slots=True)
class WordDetectionRankingRow:
    word_id: int
    word: str
    count: int


def add_detection(
    database_url: str,
    *,
    guild_id: int,
    word_id: int,
    word: str,
    user_id: int,
    channel_id: int,
    message_id: int,
    occurrence_count: int = 1,
) -> None:
    if occurrence_count <= 0:
        raise ValueError("occurrence_count must be at least 1.")

    with _connect(database_url) as connection:
        cursor = connection.cursor()
        cursor.executemany(
            """
            INSERT INTO detections (
                guild_id,
                word_id,
                word,
                user_id,
                channel_id,
                message_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                (guild_id, word_id, word, user_id, channel_id, message_id)
                for _ in range(occurrence_count)
            ],
        )


def count_detections(
    database_url: str,
    *,
    guild_id: int,
    word_id: int,
    detected_at_from: datetime | None = None,
    detected_at_to: datetime | None = None,
) -> int:
    query = [
        "SELECT COUNT(*) AS count",
        "FROM detections",
        "WHERE guild_id = %s AND word_id = %s",
    ]
    parameters: list[object] = [guild_id, word_id]

    if detected_at_from is not None:
        query.append("AND detected_at >= %s")
        parameters.append(detected_at_from)

    if detected_at_to is not None:
        query.append("AND detected_at < %s")
        parameters.append(detected_at_to)

    with _connect(database_url) as connection:
        row = connection.execute(" ".join(query), parameters).fetchone()
        assert row is not None
        return int(row["count"])


def get_detection_ranking(
    database_url: str,
    *,
    guild_id: int,
    word_id: int,
    detected_at_from: datetime | None = None,
    detected_at_to: datetime | None = None,
    limit: int = 10,
) -> list[DetectionRankingRow]:
    query = [
        "SELECT user_id, COUNT(*) AS count",
        "FROM detections",
        "WHERE guild_id = %s AND word_id = %s",
    ]
    parameters: list[object] = [guild_id, word_id]

    if detected_at_from is not None:
        query.append("AND detected_at >= %s")
        parameters.append(detected_at_from)

    if detected_at_to is not None:
        query.append("AND detected_at < %s")
        parameters.append(detected_at_to)

    query.append("GROUP BY user_id")
    query.append("ORDER BY count DESC, user_id ASC")
    query.append("LIMIT %s")
    parameters.append(limit)

    with _connect(database_url) as connection:
        rows = connection.execute(" ".join(query), parameters).fetchall()
        return [
            DetectionRankingRow(user_id=row["user_id"], count=int(row["count"]))
            for row in rows
        ]


def get_word_detection_ranking(
    database_url: str,
    *,
    guild_id: int,
    detected_at_from: datetime | None = None,
    detected_at_to: datetime | None = None,
    limit: int = 10,
) -> list[WordDetectionRankingRow]:
    query = [
        "SELECT watch_words.id AS word_id, watch_words.word, COUNT(detections.id) AS count",
        "FROM watch_words",
        "INNER JOIN detections ON detections.word_id = watch_words.id",
        "WHERE watch_words.guild_id = %s AND detections.guild_id = %s",
    ]
    parameters: list[object] = [guild_id, guild_id]

    if detected_at_from is not None:
        query.append("AND detections.detected_at >= %s")
        parameters.append(detected_at_from)

    if detected_at_to is not None:
        query.append("AND detections.detected_at < %s")
        parameters.append(detected_at_to)

    query.extend(
        [
            "GROUP BY watch_words.id, watch_words.word",
            "ORDER BY count DESC, watch_words.id ASC",
            "LIMIT %s",
        ]
    )
    parameters.append(limit)

    with _connect(database_url) as connection:
        rows = connection.execute(" ".join(query), parameters).fetchall()
        return [
            WordDetectionRankingRow(
                word_id=row["word_id"],
                word=row["word"],
                count=int(row["count"]),
            )
            for row in rows
        ]

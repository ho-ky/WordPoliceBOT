from types import SimpleNamespace
import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from commands.word import word_group
from repositories.detections import count_detections
from repositories.readings import validate_reading
from repositories.watch_words import add_watch_word, get_watch_word_by_word
from services.detection import detect_and_record_message


@pytest.mark.parametrize(
    ("word", "reading", "message", "count"),
    [
        ("生", "なま", "生で食べる。ナマでも食べる。", 2),
        ("生", "なま", "生活する。生きる。", 0),
        ("橋", None, "橋を渡って、箸で食べる。", 2),
        ("橋", None, "歩道橋を渡る。", 0),
        ("猫", None, "子猫とネコとねこじゃらし", 3),
        ("いぬ", None, "犬がいる", 1),
        ("abc", None, "猫と ＡＢＣ abc AbC", 3),
    ],
)
def test_detection_counts_matching_readings(word, reading, message, count):
    watch_word = SimpleNamespace(id=4, word=word, reading=reading)
    with (
        patch("services.detection.list_watch_words", return_value=[watch_word]),
        patch("services.detection.add_detection") as add_detection,
    ):
        matches = detect_and_record_message(
            "unused",
            guild_id=1,
            content=message,
            user_id=2,
            channel_id=3,
            message_id=5,
        )

    assert matches == ([watch_word] if count else [])
    if count:
        add_detection.assert_called_once_with(
            "unused",
            guild_id=1,
            word_id=4,
            word=word,
            user_id=2,
            channel_id=3,
            message_id=5,
            occurrence_count=count,
        )
    else:
        add_detection.assert_not_called()


def test_explicit_readings_are_normalized_and_validated():
    assert validate_reading(" ﾊｼ ") == "はし"
    with pytest.raises(ValueError):
        validate_reading("橋")


def test_reading_commands_and_counts_use_the_same_registration(db_url):
    existing = add_watch_word(
        db_url, guild_id=1, word="生", notify_enabled=True, created_by=None
    )
    message = dict(database_url=db_url, guild_id=1, user_id=2, channel_id=3)
    detect_and_record_message(**message, message_id=10, content="生で食べる")
    assert count_detections(db_url, guild_id=1, word_id=existing.id) == 1

    interaction = SimpleNamespace(
        guild_id=1,
        guild=None,
        client=SimpleNamespace(database_url=db_url, get_user=lambda _: None),
        user=SimpleNamespace(id=2),
        response=SimpleNamespace(defer=AsyncMock()),
        edit_original_response=AsyncMock(),
    )
    asyncio.run(word_group.get_command("edit").callback(interaction, word="生", reading="ナマ"))
    updated = get_watch_word_by_word(db_url, guild_id=1, word="生")
    assert (updated.id, updated.reading) == (existing.id, "なま")

    asyncio.run(word_group.get_command("add").callback(interaction, "橋", True, "ハシ"))
    asyncio.run(word_group.get_command("list").callback(interaction))
    listed = interaction.edit_original_response.call_args.kwargs["content"]
    assert "読み: なま" in listed and "読み: はし" in listed

    detect_and_record_message(**message, message_id=11, content="生活する。生とナマで食べる。")
    assert count_detections(db_url, guild_id=1, word_id=existing.id) == 3

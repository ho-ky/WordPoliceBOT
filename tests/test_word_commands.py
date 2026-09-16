from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace

from commands import word as word_commands
from commands.word import _format_watch_word, word_group
from database import initialize_database
from repositories.detections import DetectionRankingRow, WordDetectionRankingRow
from repositories.watch_words import WatchWord, add_watch_word, get_watch_word_by_word


def _command_option_names(command_name: str) -> set[str]:
    command = next(command for command in word_group.commands if command.name == command_name)
    return {parameter.display_name for parameter in command._params.values()}


def test_edit_uses_word_name_and_new_word_parameters() -> None:
    assert _command_option_names("edit") == {"word", "new_word", "notify_enabled"}


def test_delete_stats_and_ranking_use_word_name_parameter() -> None:
    assert _command_option_names("delete") == {"word"}
    assert _command_option_names("stats") == {"word", "from", "to"}
    assert _command_option_names("ranking") == {"word", "from", "to", "limit"}


def test_watch_word_display_does_not_include_internal_id() -> None:
    watch_word = WatchWord(
        id=42,
        guild_id=1,
        word="word",
        notify_enabled=True,
        created_by=None,
        created_at="2026-01-01 00:00:00",
        updated_at="2026-01-01 00:00:00",
    )

    formatted = _format_watch_word(watch_word, creator_label="管理者")

    assert formatted == "`word` | 通知: ON | 作成者: 管理者"
    assert "42" not in formatted


def test_delete_displays_deleted_word_and_removes_it(tmp_path) -> None:
    database_path = tmp_path / "delete_command.db"
    initialize_database(database_path)
    add_watch_word(
        database_path,
        guild_id=1,
        word="word",
        notify_enabled=True,
        created_by=None,
    )

    messages: list[str] = []
    interaction = SimpleNamespace(
        guild_id=1,
        client=SimpleNamespace(database_path=database_path),
        response=SimpleNamespace(send_message=messages.append),
    )

    async def send_message(message: str) -> None:
        messages.append(message)

    interaction.response.send_message = send_message
    asyncio.run(word_group.get_command("delete").callback(interaction, word="word"))

    assert messages == ["監視ワード `word` を削除しました。"]
    assert get_watch_word_by_word(database_path, guild_id=1, word="word") is None


def test_trend_renders_and_logs_competition_ranks(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    rows = [
        WordDetectionRankingRow(word_id=1, word="界隈", count=18),
        WordDetectionRankingRow(word_id=2, word="かいわい", count=18),
        WordDetectionRankingRow(word_id=3, word="Advance", count=5),
    ]
    monkeypatch.setattr(
        word_commands,
        "get_detection_word_ranking",
        lambda database_path, **kwargs: rows,
    )
    responses: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def send_message(*args: object, **kwargs: object) -> None:
        responses.append((args, kwargs))

    interaction = SimpleNamespace(
        guild_id=123,
        client=SimpleNamespace(database_path=tmp_path / "unused.db"),
        response=SimpleNamespace(send_message=send_message),
    )

    with caplog.at_level(logging.INFO, logger=word_commands.__name__):
        asyncio.run(
            word_group.get_command("trend").callback(
                interaction,
                from_date=None,
                to_date=None,
                limit=10,
            )
        )

    assert len(responses) == 1
    embed = responses[0][1]["embed"]
    assert embed.description.splitlines()[1:] == [
        "1. `界隈` 18回",
        "1. `かいわい` 18回",
        "3. `Advance` 5回",
    ]
    assert (
        "rows=[(1, '界隈', 18), (2, 'かいわい', 18), (3, 'Advance', 5)]"
        in caplog.text
    )
    assert "ranks=[1, 1, 3]" in caplog.text


def test_ranking_renders_and_logs_competition_ranks(
    tmp_path,
    monkeypatch,
    caplog,
) -> None:
    database_path = tmp_path / "ranking_command.db"
    initialize_database(database_path)
    add_watch_word(
        database_path,
        guild_id=123,
        word="sample",
        notify_enabled=True,
        created_by=None,
    )
    rows = [
        DetectionRankingRow(user_id=101, count=6),
        DetectionRankingRow(user_id=102, count=6),
        DetectionRankingRow(user_id=103, count=4),
        DetectionRankingRow(user_id=104, count=2),
    ]
    monkeypatch.setattr(
        word_commands,
        "get_word_detection_ranking",
        lambda database_path, **kwargs: rows,
    )
    responses: list[tuple[tuple[object, ...], dict[str, object]]] = []

    async def send_message(*args: object, **kwargs: object) -> None:
        responses.append((args, kwargs))

    interaction = SimpleNamespace(
        guild_id=123,
        client=SimpleNamespace(database_path=database_path),
        response=SimpleNamespace(send_message=send_message),
    )

    with caplog.at_level(logging.INFO, logger=word_commands.__name__):
        asyncio.run(
            word_group.get_command("ranking").callback(
                interaction,
                word="sample",
                from_date=None,
                to_date=None,
                limit=10,
            )
        )

    assert len(responses) == 1
    embed = responses[0][1]["embed"]
    assert embed.description.splitlines()[1:] == [
        "1. <@101> 6回",
        "1. <@102> 6回",
        "3. <@103> 4回",
        "4. <@104> 2回",
    ]
    assert "rows=[(101, 6), (102, 6), (103, 4), (104, 2)]" in caplog.text
    assert "ranks=[1, 1, 3, 4]" in caplog.text

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from commands.word import _format_watch_word, word_group
from repositories.watch_words import WatchWord
from repositories.watch_words import add_watch_word, get_watch_word_by_word
from database import initialize_database
from repositories.watch_words import WatchWord


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

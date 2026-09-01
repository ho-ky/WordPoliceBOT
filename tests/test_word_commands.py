from __future__ import annotations

from commands.word import _format_watch_word, word_group
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

import asyncio
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from bot import sync_application_commands


def test_guild_mode_removes_old_global_commands_after_guild_sync():
    tree = MagicMock()
    tree.sync = AsyncMock(return_value=[])

    asyncio.run(sync_application_commands(tree, 12345))

    guild = tree.copy_global_to.call_args.kwargs["guild"]
    assert guild.id == 12345
    assert tree.sync.await_args_list == [call(guild=guild), call()]
    tree.clear_commands.assert_called_once_with(guild=None)
    assert tree.mock_calls.index(call.sync(guild=guild)) < tree.mock_calls.index(
        call.clear_commands(guild=None)
    ) < tree.mock_calls.index(call.sync())


def test_global_mode_does_not_clear_global_commands():
    tree = MagicMock()
    tree.sync = AsyncMock(return_value=[])

    asyncio.run(sync_application_commands(tree, None))

    tree.sync.assert_awaited_once_with()
    tree.copy_global_to.assert_not_called()
    tree.clear_commands.assert_not_called()


def test_failed_guild_sync_does_not_remove_global_commands():
    tree = MagicMock()
    tree.sync = AsyncMock(side_effect=RuntimeError("guild sync failed"))

    with pytest.raises(RuntimeError, match="guild sync failed"):
        asyncio.run(sync_application_commands(tree, 12345))

    tree.clear_commands.assert_not_called()
    tree.sync.assert_awaited_once()

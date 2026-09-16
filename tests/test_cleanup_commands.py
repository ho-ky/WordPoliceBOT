import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

import discord

from cleanup_commands import remove_guild_duplicates


def command(name, kind=discord.AppCommandType.chat_input):
    return SimpleNamespace(name=name, type=kind, delete=AsyncMock())


def test_removes_only_duplicates_in_requested_guild():
    global_commands = [command("ping"), command("word")]
    duplicates = [command("ping"), command("word")]
    unrelated = [command("guild_only"), command("word", discord.AppCommandType.user)]
    tree = SimpleNamespace(fetch_commands=AsyncMock(side_effect=[
        global_commands, duplicates + unrelated,
    ]))
    guild = discord.Object(id=123)

    assert asyncio.run(remove_guild_duplicates(tree, guild)) == ["ping", "word"]
    assert tree.fetch_commands.await_args_list == [call(), call(guild=guild)]
    for item in duplicates:
        item.delete.assert_awaited_once_with()
    for item in global_commands + unrelated:
        item.delete.assert_not_awaited()


def test_no_global_registration_preserves_guild_commands():
    item = command("word")
    tree = SimpleNamespace(fetch_commands=AsyncMock(side_effect=[[], [item]]))
    assert asyncio.run(remove_guild_duplicates(tree, discord.Object(id=123))) == []
    item.delete.assert_not_awaited()


def test_repeated_cleanup_is_noop_after_duplicates_removed():
    tree = SimpleNamespace(fetch_commands=AsyncMock(side_effect=[[command("word")], []]))
    assert asyncio.run(remove_guild_duplicates(tree, discord.Object(id=123))) == []

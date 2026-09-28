"""Remove stale guild duplicates after switching to global commands."""

from __future__ import annotations

import argparse
import asyncio

import discord

from config import load_settings


async def remove_guild_duplicates(tree, guild: discord.Object) -> list[str]:
    global_commands = await tree.fetch_commands()
    global_keys = {(command.name, command.type) for command in global_commands}
    removed = []
    for command in await tree.fetch_commands(guild=guild):
        if (command.name, command.type) in global_keys:
            await command.delete()
            removed.append(command.name)
    return removed


async def main(guild_id: int) -> None:
    settings = load_settings()
    if settings.command_guild_id is not None:
        raise RuntimeError("Cleanup requires global command mode (COMMAND_GUILD_ID unset).")
    async with discord.Client(intents=discord.Intents.none()) as client:
        await client.login(settings.discord_token)
        tree = discord.app_commands.CommandTree(client)
        removed = await remove_guild_duplicates(tree, discord.Object(id=guild_id))
        print(f"Removed guild duplicates: {removed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guild-id", type=int, required=True)
    asyncio.run(main(parser.parse_args().guild_id))

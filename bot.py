from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from config import Settings, load_settings
from database import initialize_database
from commands.word import word_group
from services.detection import detect_and_record_message


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class WordPoliceBot(commands.Bot):
    def __init__(self, *, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.settings = settings
        self.database_path = settings.database_path

    async def setup_hook(self) -> None:
        await asyncio.to_thread(initialize_database, self.settings.database_path)

        if self.settings.command_guild_id is not None:
            guild = discord.Object(id=self.settings.command_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if not message.content:
            return

        try:
            matched_words = await asyncio.to_thread(
                detect_and_record_message,
                self.settings.database_path,
                guild_id=message.guild.id,
                content=message.content,
                user_id=message.author.id,
                channel_id=message.channel.id,
                message_id=message.id,
            )
        except Exception:
            logging.exception("failed to detect words for message %s", message.id)
            return

        notify_words = [word.word for word in matched_words if word.notify_enabled]
        if not notify_words:
            return

        reply_text = "「" + "」「".join(notify_words) + "」が検出されました。"
        try:
            await message.reply(reply_text, mention_author=False)
        except discord.Forbidden:
            logging.warning("failed to reply to message %s due to missing permissions", message.id)
        except discord.HTTPException:
            logging.exception("failed to reply to message %s", message.id)


@discord.app_commands.command(name="ping", description="Bot の起動確認を行います")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("pong", ephemeral=True)


async def main() -> None:
    settings = load_settings()
    bot = WordPoliceBot(settings=settings)
    bot.tree.add_command(ping)
    bot.tree.add_command(word_group)

    async with bot:
        await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())

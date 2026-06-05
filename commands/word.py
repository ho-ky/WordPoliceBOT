from __future__ import annotations

from pathlib import Path
import sqlite3

import discord
from discord import app_commands

from repositories.watch_words import (
    WatchWord,
    add_watch_word,
    delete_watch_word,
    list_watch_words,
    update_watch_word,
)


word_group = app_commands.Group(name="word", description="監視ワードを管理します")


def _get_database_path(interaction: discord.Interaction) -> Path:
    database_path = getattr(interaction.client, "database_path", None)
    if not isinstance(database_path, Path):
        raise RuntimeError("database_path is not configured on the bot.")
    return database_path


def _format_watch_word(word: WatchWord) -> str:
    status = "ON" if word.notify_enabled else "OFF"
    creator = f"<@{word.created_by}>" if word.created_by is not None else "unknown"
    return f"`{word.id}` | `{word.word}` | notify:{status} | created_by:{creator}"


@word_group.command(name="add", description="監視ワードを追加します")
@app_commands.guild_only()
@app_commands.describe(word="登録する単語", notify_enabled="検出時の返信を有効にするか")
async def add(
    interaction: discord.Interaction,
    word: str,
    notify_enabled: bool = True,
) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    try:
        created_word = add_watch_word(
            database_path,
            guild_id=interaction.guild_id,
            word=word,
            notify_enabled=notify_enabled,
            created_by=interaction.user.id,
        )
    except ValueError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return
    except sqlite3.IntegrityError:
        await interaction.response.send_message("同じ監視ワードはすでに登録されています。", ephemeral=True)
        return
    except Exception as exc:
        await interaction.response.send_message(f"登録に失敗しました: {exc}", ephemeral=True)
        return

    await interaction.response.send_message(
        f"監視ワードを追加しました: {_format_watch_word(created_word)}",
        ephemeral=True,
    )


@word_group.command(name="list", description="監視ワード一覧を表示します")
@app_commands.guild_only()
async def word_list(interaction: discord.Interaction) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)
    words = list_watch_words(database_path, guild_id=interaction.guild_id)

    if not words:
        await interaction.response.send_message("登録済みの監視ワードはありません。", ephemeral=True)
        return

    lines = ["監視ワード一覧:"]
    lines.extend(_format_watch_word(word) for word in words)
    await interaction.response.send_message("\n".join(lines), ephemeral=True)


@word_group.command(name="edit", description="監視ワードを編集します")
@app_commands.guild_only()
@app_commands.describe(
    word_id="編集する監視ワードのID",
    word="新しい単語",
    notify_enabled="検出時の返信を有効にするか",
)
async def edit(
    interaction: discord.Interaction,
    word_id: int,
    word: str | None = None,
    notify_enabled: bool | None = None,
) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    try:
        updated_word = update_watch_word(
            database_path,
            guild_id=interaction.guild_id,
            word_id=word_id,
            word=word,
            notify_enabled=notify_enabled,
        )
    except ValueError as exc:
        await interaction.response.send_message(str(exc), ephemeral=True)
        return
    except LookupError:
        await interaction.response.send_message("指定した監視ワードが見つかりません。", ephemeral=True)
        return
    except sqlite3.IntegrityError:
        await interaction.response.send_message("同じ監視ワードはすでに登録されています。", ephemeral=True)
        return
    except Exception as exc:
        await interaction.response.send_message(f"更新に失敗しました: {exc}", ephemeral=True)
        return

    await interaction.response.send_message(
        f"監視ワードを更新しました: {_format_watch_word(updated_word)}",
        ephemeral=True,
    )


@word_group.command(name="delete", description="監視ワードを削除します")
@app_commands.guild_only()
@app_commands.describe(word_id="削除する監視ワードのID")
async def delete(interaction: discord.Interaction, word_id: int) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    deleted = delete_watch_word(database_path, guild_id=interaction.guild_id, word_id=word_id)
    if not deleted:
        await interaction.response.send_message("指定した監視ワードが見つかりません。", ephemeral=True)
        return

    await interaction.response.send_message("監視ワードを削除しました。", ephemeral=True)

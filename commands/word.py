from __future__ import annotations

from pathlib import Path
import sqlite3

import discord
from discord import app_commands

from repositories.detections import DetectionRankingRow, WordDetectionRankingRow
from repositories.watch_words import (
    WatchWord,
    add_watch_word,
    delete_watch_word,
    get_watch_word_by_word,
    list_watch_words,
    update_watch_word,
)
from services.stats import (
    DEFAULT_RANKING_LIMIT,
    get_detection_word_ranking,
    get_word_detection_count,
    get_word_detection_ranking,
    validate_ranking_options,
)

from datetime import datetime
from zoneinfo import ZoneInfo


word_group = app_commands.Group(name="word", description="監視ワードを管理します")


def _get_database_path(interaction: discord.Interaction) -> Path:
    database_path = getattr(interaction.client, "database_path", None)
    if not isinstance(database_path, Path):
        raise RuntimeError("database_path is not configured on the bot.")
    return database_path


async def _get_creator_label(interaction: discord.Interaction, user_id: int | None) -> str:
    if user_id is None:
        return "unknown"

    if interaction.guild is not None:
        member = interaction.guild.get_member(user_id)
        if member is not None:
            return member.display_name
        try:
            member = await interaction.guild.fetch_member(user_id)
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            member = None
        if member is not None:
            return member.display_name

    user = interaction.client.get_user(user_id)
    if user is not None:
        return user.display_name

    return "unknown"


def _format_watch_word(word: WatchWord, *, creator_label: str) -> str:
    status = "ON" if word.notify_enabled else "OFF"
    return f"`{word.word}` | 通知: {status} | 作成者: {creator_label}"


def _to_discord_timestamp(date_str: str) -> str:
    """文字列の日付をDiscord用タイムスタンプ構文に変換する"""
    try:
        # ハイフンが含まれているかでフォーマットを動的に判定
        if "-" in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            # 20260606 のようなハイフンなし(8桁)の入力に対応
            dt = datetime.strptime(date_str, "%Y%m%d")
            
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
        unix_ts = int(dt.timestamp())
        
        return f"<t:{unix_ts}:d>"
        
    except ValueError:
        # 想定外の入力（例: "あいうえお"など）が来た場合はそのまま返す
        return date_str.replace('-', '/')

def _format_period(from_date: str | None, to_date: str | None) -> str:
    if from_date is None and to_date is None:
        return "全期間"

    # ヘルパー関数を通してDiscord用文字列に変換
    from_str = _to_discord_timestamp(from_date) if from_date else None
    to_str = _to_discord_timestamp(to_date) if to_date else None

    if from_str and to_str:
        return f"{from_str} から {to_str} まで"
    if from_str:
        return f"{from_str} 以降"
    return f"{to_str} 以前"


def _format_ranking_line(rank: int, row: DetectionRankingRow) -> str:
    return f"{rank}. <@{row.user_id}> {row.count}回"


def _competition_ranks(counts: list[int]) -> list[int]:
    ranks: list[int] = []
    previous_count: int | None = None
    rank = 0

    for index, count in enumerate(counts, start=1):
        if count != previous_count:
            rank = index
            previous_count = count
        ranks.append(rank)

    return ranks


def _format_word_ranking_lines(rows: list[WordDetectionRankingRow]) -> list[str]:
    return [
        f"{rank}. `{row.word}` {row.count}回"
        for rank, row in zip(_competition_ranks([row.count for row in rows]), rows)
    ]


@word_group.command(name="add", description="監視ワードを追加します")
@app_commands.guild_only()
@app_commands.describe(word="登録する単語", notify_enabled="検出時の返信を有効にするか")
async def add(
    interaction: discord.Interaction,
    word: str,
    notify_enabled: bool,
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
        await interaction.response.send_message(str(exc))
        return
    except sqlite3.IntegrityError:
        await interaction.response.send_message("同じ監視ワードはすでに登録されています。")
        return
    except Exception as exc:
        await interaction.response.send_message(f"登録に失敗しました: {exc}", ephemeral=True)
        return

    creator_label = await _get_creator_label(interaction, created_word.created_by)
    await interaction.response.send_message(
        f"監視ワードを追加しました: {_format_watch_word(created_word, creator_label=creator_label)}",
    )


@word_group.command(name="list", description="監視ワード一覧を表示します")
@app_commands.guild_only()
async def word_list(interaction: discord.Interaction) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)
    words = list_watch_words(database_path, guild_id=interaction.guild_id)

    if not words:
        await interaction.response.send_message("登録済みの監視ワードはありません。")
        return

    lines = ["監視ワード一覧:"]
    for word in words:
        creator_label = await _get_creator_label(interaction, word.created_by)
        lines.append(_format_watch_word(word, creator_label=creator_label))
    await interaction.response.send_message("\n".join(lines))


@word_group.command(name="edit", description="監視ワードを編集します")
@app_commands.guild_only()
@app_commands.describe(
    word="編集する監視ワード",
    new_word="新しい単語",
    notify_enabled="検出時の返信を有効にするか",
)
async def edit(
    interaction: discord.Interaction,
    word: str,
    new_word: str | None = None,
    notify_enabled: bool | None = None,
) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    try:
        watch_word = get_watch_word_by_word(
            database_path,
            guild_id=interaction.guild_id,
            word=word,
        )
        if watch_word is None:
            raise LookupError
        updated_word = update_watch_word(
            database_path,
            guild_id=interaction.guild_id,
            word_id=watch_word.id,
            word=new_word,
            notify_enabled=notify_enabled,
        )
    except ValueError as exc:
        await interaction.response.send_message(str(exc))
        return
    except LookupError:
        await interaction.response.send_message("指定した監視ワードが見つかりません。")
        return
    except sqlite3.IntegrityError:
        await interaction.response.send_message("同じ監視ワードはすでに登録されています。")
        return
    except Exception as exc:
        await interaction.response.send_message(f"更新に失敗しました: {exc}", ephemeral=True)
        return

    creator_label = await _get_creator_label(interaction, updated_word.created_by)
    await interaction.response.send_message(
        f"監視ワードを更新しました: {_format_watch_word(updated_word, creator_label=creator_label)}",
    )


@word_group.command(name="delete", description="監視ワードを削除します")
@app_commands.guild_only()
@app_commands.describe(word="削除する監視ワード")
async def delete(interaction: discord.Interaction, word: str) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    watch_word = get_watch_word_by_word(
        database_path,
        guild_id=interaction.guild_id,
        word=word,
    )
    if watch_word is None:
        await interaction.response.send_message("指定した監視ワードが見つかりません。")
        return

    deleted = delete_watch_word(
        database_path,
        guild_id=interaction.guild_id,
        word_id=watch_word.id,
    )
    if not deleted:
        await interaction.response.send_message("指定した監視ワードが見つかりません。")
        return

    await interaction.response.send_message("監視ワードを削除しました。")


@word_group.command(name="stats", description="監視ワードの検出数を集計します")
@app_commands.guild_only()
@app_commands.describe(
    word="集計する監視ワード",
    from_date="集計開始日 (YYYY-MM-DD)",
    to_date="集計終了日 (YYYY-MM-DD)",
)
@app_commands.rename(from_date="from", to_date="to")
async def stats(
    interaction: discord.Interaction,
    word: str,
    from_date: str | None = None,
    to_date: str | None = None,
) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    try:
        watch_word = get_watch_word_by_word(
            database_path,
            guild_id=interaction.guild_id,
            word=word,
        )
        if watch_word is None:
            raise LookupError
        count = get_word_detection_count(
            database_path,
            guild_id=interaction.guild_id,
            word_id=watch_word.id,
            from_date=from_date,
            to_date=to_date,
        )
    except LookupError:
        await interaction.response.send_message("指定した監視ワードが見つかりません。")
        return
    except ValueError as exc:
        await interaction.response.send_message(str(exc))
        return
    except Exception as exc:
        await interaction.response.send_message(f"集計に失敗しました: {exc}", ephemeral=True)
        return

    period_label = _format_period(from_date, to_date)
    await interaction.response.send_message(
        f"`{watch_word.word}` の検出数: {count}回\n対象期間: {period_label}",
    )


@word_group.command(name="ranking", description="最も多く監視ワードを発言した「ユーザー」のランキングを表示します")
@app_commands.guild_only()
@app_commands.describe(
    word="集計する監視ワード",
    from_date="集計開始日 (YYYY-MM-DD)",
    to_date="集計終了日 (YYYY-MM-DD)",
    limit="表示件数",
)
@app_commands.rename(from_date="from", to_date="to")
async def ranking(
    interaction: discord.Interaction,
    word: str,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    try:
        watch_word = get_watch_word_by_word(
            database_path,
            guild_id=interaction.guild_id,
            word=word,
        )
        if watch_word is None:
            raise LookupError
        validated_limit, validation_errors = validate_ranking_options(
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )
        if validation_errors:
            error_lines = "\n".join(f"- {error}" for error in validation_errors)
            await interaction.response.send_message(
                f"入力内容に問題があります:\n{error_lines}",
            )
            return
        assert validated_limit is not None
        rows = get_word_detection_ranking(
            database_path,
            guild_id=interaction.guild_id,
            word_id=watch_word.id,
            from_date=from_date,
            to_date=to_date,
            limit=validated_limit,
        )
    except LookupError:
        await interaction.response.send_message("指定した監視ワードが見つかりません。")
        return
    except ValueError as exc:
        await interaction.response.send_message(str(exc))
        return
    except Exception as exc:
        await interaction.response.send_message(f"集計に失敗しました: {exc}", ephemeral=True)
        return

    if not rows:
        await interaction.response.send_message(
            f"`{watch_word.word}` の対象期間内の検出はありません。",
        )
        return

    period_label = _format_period(from_date, to_date)
    lines = [f"`{watch_word.word}` のランキング ({period_label}, 上位{validated_limit}件)"]
    lines.extend(
        _format_ranking_line(rank, row)
        for rank, row in zip(_competition_ranks([row.count for row in rows]), rows)
    )
    embed = discord.Embed(title="検出ランキング", description="\n".join(lines))
    await interaction.response.send_message(embed=embed)


@word_group.command(name="trend", description="最も多く検出された「言葉」のランキングを表示します")
@app_commands.guild_only()
@app_commands.describe(
    from_date="集計開始日 (YYYY-MM-DD)",
    to_date="集計終了日 (YYYY-MM-DD)",
    limit="表示件数",
)
@app_commands.rename(from_date="from", to_date="to")
async def trend(
    interaction: discord.Interaction,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
) -> None:
    assert interaction.guild_id is not None
    database_path = _get_database_path(interaction)

    validated_limit, validation_errors = validate_ranking_options(
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    if validation_errors:
        error_lines = "\n".join(f"- {error}" for error in validation_errors)
        await interaction.response.send_message(
            f"入力内容に問題があります:\n{error_lines}",
        )
        return

    assert validated_limit is not None
    try:
        rows = get_detection_word_ranking(
            database_path,
            guild_id=interaction.guild_id,
            from_date=from_date,
            to_date=to_date,
            limit=validated_limit,
        )
    except Exception as exc:
        await interaction.response.send_message(f"集計に失敗しました: {exc}")
        return

    if not rows:
        await interaction.response.send_message("対象期間内の検出はありません。")
        return

    period_label = _format_period(from_date, to_date)
    lines = [f"単語別検出ランキング ({period_label}, 上位{validated_limit}件)"]
    lines.extend(_format_word_ranking_lines(rows))
    embed = discord.Embed(title="単語別検出ランキング", description="\n".join(lines))
    await interaction.response.send_message(embed=embed)

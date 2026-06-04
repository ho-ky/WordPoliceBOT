from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    database_path: Path
    command_guild_id: int | None


def load_settings() -> Settings:
    load_dotenv()

    discord_token = os.getenv("DISCORD_TOKEN", "").strip()
    if not discord_token:
        raise RuntimeError("DISCORD_TOKEN is required.")

    database_path = Path(os.getenv("DATABASE_PATH", "data/wordpolice.db")).expanduser()

    command_guild_id_raw = os.getenv("COMMAND_GUILD_ID", "").strip()
    command_guild_id = int(command_guild_id_raw) if command_guild_id_raw else None

    return Settings(
        discord_token=discord_token,
        database_path=database_path,
        command_guild_id=command_guild_id,
    )

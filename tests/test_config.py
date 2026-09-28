from __future__ import annotations

import pytest

import config


def test_load_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        config.load_settings()


def test_load_settings_accepts_guild_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("DISCORD_TOKEN", "test-token")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    monkeypatch.setenv("COMMAND_GUILD_ID", "12345")

    settings = config.load_settings()

    assert settings.database_url == "postgresql://localhost/test"
    assert settings.command_guild_id == 12345

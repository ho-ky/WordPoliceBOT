from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database import initialize_database
from repositories.watch_words import _connect, add_watch_word, list_watch_words


def test_initialize_sets_wal(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    initialize_database(db_path)

    # Open a new connection and read PRAGMA journal_mode
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("PRAGMA journal_mode;")
        mode = cur.fetchone()[0]
    assert str(mode).lower() == "wal"


def test_connect_enables_foreign_keys(tmp_path: Path) -> None:
    db_path = tmp_path / "test2.db"
    initialize_database(db_path)

    conn = _connect(db_path)
    try:
        cur = conn.execute("PRAGMA foreign_keys;")
        enabled = cur.fetchone()[0]
    finally:
        conn.close()

    assert int(enabled) == 1


def test_add_watch_word_keeps_original_display_value(tmp_path: Path) -> None:
    db_path = tmp_path / "test3.db"
    initialize_database(db_path)

    input_word = "ＡＢＣabc　"
    created = add_watch_word(
        db_path, guild_id=1, word=input_word, notify_enabled=True, created_by=None
    )

    # Stored word should preserve the original trimmed display value (strip applied)
    assert created.word == input_word.strip()


def test_detection_normalization_not_implemented() -> None:
    pytest.skip("検出ハンドラが未実装のため、判定時の正規化はテスト不可")

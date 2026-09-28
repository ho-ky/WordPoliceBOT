from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def postgres_test_url():
    admin_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    database_name = f"wordpolice_test_{uuid4().hex[:12]}"
    test_url = make_conninfo(admin_url, dbname=database_name)

    with psycopg.connect(admin_url, autocommit=True) as connection:
        connection.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
        )
    try:
        migration = (
            ROOT / "supabase/migrations/20260928022746_create_wordpolice_schema.sql"
        )
        with psycopg.connect(test_url) as connection:
            connection.execute(migration.read_text(encoding="utf-8"), prepare=False)
        yield test_url
    finally:
        with psycopg.connect(admin_url, autocommit=True) as connection:
            connection.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    sql.Identifier(database_name)
                )
            )


@pytest.fixture
def db_url(postgres_test_url):
    with psycopg.connect(postgres_test_url) as connection:
        connection.execute(
            "TRUNCATE TABLE public.detections, public.watch_words, "
            "public.guild_settings RESTART IDENTITY CASCADE"
        )
    return postgres_test_url

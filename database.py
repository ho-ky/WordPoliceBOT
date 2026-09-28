from __future__ import annotations

import psycopg
from psycopg.rows import dict_row


def connect(database_url: str) -> psycopg.Connection:
    return psycopg.connect(database_url, row_factory=dict_row, connect_timeout=10)


def check_database_connection(database_url: str) -> None:
    with connect(database_url) as connection:
        connection.execute("SELECT 1 FROM public.watch_words LIMIT 0")
        connection.execute("SELECT 1 FROM public.detections LIMIT 0")

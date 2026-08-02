# database/connection.py

import sqlite3
from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent.parent

DATABASE_PATH = (
    BASE_DIR
    / "data"
    / "clinic_database.db"
)


def get_connection() -> sqlite3.Connection:

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA busy_timeout = 30000"
    )

    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    return connection


def execute_query(
    query: str,
    parameters: tuple = (),
):

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            parameters,
        )

        connection.commit()

        return cursor


def fetch_one(
    query: str,
    parameters: tuple = (),
):

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            parameters,
        )

        return cursor.fetchone()


def fetch_all(
    query: str,
    parameters: tuple = (),
):

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            parameters,
        )

        return cursor.fetchall()
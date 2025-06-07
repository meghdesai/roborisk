from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from polygon import RESTClient

from .config import get_settings

DB_PATH = Path(__file__).resolve().parent / "prices.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS prices("
        "ticker TEXT,"
        " ts_utc INTEGER,"
        " open REAL,"
        " high REAL,"
        " low REAL,"
        " close REAL,"
        " volume INTEGER,"
        " PRIMARY KEY(ticker, ts_utc)"
        ")"
    )
    return conn



def fetch_daily_bars(ticker: str, start: str, end: str) -> Iterable:
    settings = get_settings()
    client = RESTClient(api_key=settings.POLYGON_API_KEY)
    return client.list_aggs(ticker, 1, "day", start, end)


def ingest(
    tickers: list[str], start: str = "2023-03-01", end: str = "2023-06-07"
) -> None:
    conn = _get_connection()
    cur = conn.cursor()
    for ticker in tickers:
        for bar in fetch_daily_bars(ticker, start, end):
            cur.execute(
                "INSERT OR REPLACE INTO prices VALUES (?,?,?,?,?,?,?)",
                (
                    ticker,
                    bar.timestamp,
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                ),
            )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys

    ingest(sys.argv[1:])

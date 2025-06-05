from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
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


def fetch_minute_bars(ticker: str, lookback_min: int = 1) -> Iterable:
    settings = get_settings()
    client = RESTClient(api_key=settings.POLYGON_API_KEY)
    end = datetime.now(tz=timezone.utc)
    start = end - timedelta(minutes=lookback_min)
    return client.list_aggs(
        ticker,
        1,
        "minute",
        int(start.timestamp()),
        int(end.timestamp()),
    )


def ingest(tickers: list[str]) -> None:
    conn = _get_connection()
    cur = conn.cursor()
    for ticker in tickers:
        for bar in fetch_minute_bars(ticker, lookback_min=60):
            cur.execute(
                "INSERT OR IGNORE INTO prices VALUES (?,?,?,?,?,?,?)",
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

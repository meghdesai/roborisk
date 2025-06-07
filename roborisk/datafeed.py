# roborisk/datafeed.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List

from polygon import RESTClient

from .config import get_settings

DB_PATH = Path(__file__).resolve().parents[1] / "prices.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            ticker  TEXT,
            ts_utc  INTEGER,
            open    REAL,
            high    REAL,
            low     REAL,
            close   REAL,
            volume  INTEGER,
            PRIMARY KEY (ticker, ts_utc)
        )
        """
    )
    return conn


def fetch_daily_bars(ticker: str, start: str, end: str) -> Iterable:
    """Fetch daily bars for ``ticker`` between ``start`` and ``end`` (inclusive)."""
    settings = get_settings()
    client = RESTClient(api_key=settings.POLYGON_API_KEY)

    return client.list_aggs(
        ticker=ticker,
        multiplier=1,
        timespan="day",
        from_=start,
        to=end,
    )


def ingest(tickers: List[str], start: str = "2023-03-01", end: str = "2023-06-07") -> None:
    conn = _get_connection()
    cur = conn.cursor()

    for ticker in tickers:
        for bar in fetch_daily_bars(ticker, start, end):
            cur.execute(
                "INSERT OR IGNORE INTO prices VALUES (?,?,?,?,?,?,?)",
                (
                    ticker,
                    bar.timestamp,  # ms since epoch (already in bar)
                    bar.open,
                    bar.high,
                    bar.low,
                    bar.close,
                    bar.volume,
                ),
            )
        print(f"✅ {ticker} up-to-date")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys

    # Example: python -m roborisk.datafeed AAPL MSFT
    ingest(sys.argv[1:] or ["AAPL"])  # default date range

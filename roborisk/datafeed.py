# roborisk/datafeed.py
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List

from polygon import RESTClient

from .config import get_settings

DB_PATH = Path(__file__).resolve().parent / "prices.db"


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


def fetch_daily_bars(ticker: str, lookback_days: int = 5) -> Iterable:
    """
    Free-tier helper: returns up to `lookback_days` daily bars
    *ending yesterday* so we never query the still-open session.
    """
    settings = get_settings()
    client = RESTClient(api_key=settings.POLYGON_API_KEY)

    end: date = datetime.now(tz=timezone.utc).date() - timedelta(days=1)
    start: date = end - timedelta(days=lookback_days - 1)

    # ISO-8601 strings are the documented format
    return client.list_aggs(
        ticker=ticker,
        multiplier=1,
        timespan="day",        # ← daily bars are free
        from_=start.isoformat(),
        to=end.isoformat(),
        limit=lookback_days,
    )


def ingest(tickers: List[str], lookback_days: int = 5) -> None:
    conn = _get_connection()
    cur = conn.cursor()

    for ticker in tickers:
        for bar in fetch_daily_bars(ticker, lookback_days):
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

    # Example: python -m roborisk.datafeed AAPL MSFT NVDA -- ingests last 5 days
    ingest(sys.argv[1:] or ["AAPL"])

# roborisk/datafeed.py
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List

from pymongo import MongoClient, ASCENDING

import pandas as pd
import yfinance as yf

from .config import get_settings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

def _get_collection():
    settings = get_settings()
    client = MongoClient(settings.MONGODB_URI)
    db = client["roborisk"]
    coll = db["prices"]
    coll.create_index([("ticker", ASCENDING), ("ts_utc", ASCENDING)], unique=True)
    return coll


def fetch_daily_bars(ticker: str, start: str, end: str) -> Iterable[dict]:
    """Fetch daily bars for ``ticker`` between ``start`` and ``end`` (inclusive)
    from Yahoo Finance."""

    df = yf.download(
        tickers=ticker,
        start=start,
        end=(pd.to_datetime(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
        progress=False,
        interval="1d",
        auto_adjust=True, 
    )

    df = df.reset_index()
    df.rename(columns=str.lower, inplace=True)
    df["timestamp"] = df["date"].astype("int64") // 10**6
    for _, row in df.iterrows():
        yield {
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
            "timestamp": int(row["timestamp"]),
        }

DEFAULT_END = date(2024, 1, 31)
DEFAULT_START = DEFAULT_END - timedelta(days=359)


def ingest(
    tickers: List[str],
    start: str = DEFAULT_START.isoformat(),
    end: str = DEFAULT_END.isoformat(),
) -> None:
    coll = _get_collection()

    for ticker in tickers:
        for bar in fetch_daily_bars(ticker, start, end):
            coll.update_one(
                {"ticker": ticker, "ts_utc": bar["timestamp"]},
                {
                    "$set": {
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": float(bar["volume"]),
                    }
                },
                upsert=True,
            )
        print(f"✅ {ticker} up-to-date")


def ingest_date_range(ticker: str, start: str, end: str) -> None:
    """Convenience wrapper to ingest data for a single ``ticker`` between the
    provided ``start`` and ``end`` dates."""

    ingest([ticker], start=start, end=end)


if __name__ == "__main__":
    import sys

    # Example: python -m roborisk.datafeed AAPL MSFT
    ingest(sys.argv[1:] or ["AAPL"])  # default date range

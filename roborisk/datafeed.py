# roborisk/datafeed.py
from __future__ import annotations

from typing import Iterable, List

from pymongo import MongoClient, ASCENDING

from polygon import RESTClient

from .config import get_settings


def _get_collection():
    settings = get_settings()
    client = MongoClient(settings.MONGODB_URI)
    db = client["roborisk"]
    coll = db["prices"]
    coll.create_index([("ticker", ASCENDING), ("ts_utc", ASCENDING)], unique=True)
    return coll


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
    coll = _get_collection()

    for ticker in tickers:
        for bar in fetch_daily_bars(ticker, start, end):
            coll.update_one(
                {"ticker": ticker, "ts_utc": bar.timestamp},
                {
                    "$set": {
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                    }
                },
                upsert=True,
            )
        print(f"✅ {ticker} up-to-date")


if __name__ == "__main__":
    import sys

    # Example: python -m roborisk.datafeed AAPL MSFT
    ingest(sys.argv[1:] or ["AAPL"])  # default date range

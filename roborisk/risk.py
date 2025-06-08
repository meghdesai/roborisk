import csv
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import Union
import numpy as np

from .config import get_settings


def _get_collection():
    settings = get_settings()
    client = MongoClient(settings.MONGODB_URI)
    db = client["roborisk"]
    return db["prices"]


def _load_portfolio(path: str):
    tickers = []
    shares = []
    with open(path) as f:
        for row in csv.reader(f):
            if not row:
                continue
            tickers.append(row[0])
            shares.append(float(row[1]))
    return tickers, np.array(shares, dtype=float)


# risk.py  (replace the helper)
def _get_returns_and_price(ticker: str,
                           as_of_dt: datetime,
                           lookback_days: int):
    """
    Return log-returns and close price *ending exactly on as_of_dt*.
    The query window is [as_of_dt-lookback_days, as_of_dt] inclusive.
    """
    next_midnight = as_of_dt + timedelta(days=1)
    end_exclusive = int(next_midnight.timestamp() * 1000)

    coll = _get_collection()
    cursor = (coll.find(
        {"ticker": ticker, "ts_utc": {"$lt": end_exclusive}},
        {"_id": 0, "ts_utc": 1, "close": 1},
    )
    .sort("ts_utc", -1)
    .limit(lookback_days + 1))

    rows = list(cursor)[::-1]
    must_have = int(as_of_dt.timestamp() * 1000)
    if not rows or rows[-1]["ts_utc"] < must_have:
        raise ValueError(f"no close for {ticker} on {as_of_dt.date()}")
    closes = np.array([r["close"] for r in rows], float)
    returns = np.diff(np.log(closes))
    return returns, closes[-1]


def monte_carlo_var(
    portfolio_path: str,
    as_of: Union[str, datetime] = "2023-06-07",   # <-- accept dt object too
    lookback_days: int = 60,
    simulations: int = 1000,
    alpha: float = 0.95,
):
    if isinstance(as_of, str):
        as_of_dt = datetime.fromisoformat(as_of)
    else:
        as_of_dt = as_of
        
    tickers, shares = _load_portfolio(portfolio_path)

    returns_list = []
    prices = []
    for t in tickers:
        r, p = _get_returns_and_price(t, as_of_dt, lookback_days)
        returns_list.append(r)
        prices.append(p)

    returns = np.column_stack(returns_list)
    prices = np.array(prices)
    weights = shares * prices
    port_value = weights.sum()
    weights = weights / port_value

    mu = returns.mean(axis=0)
    cov = np.cov(returns, rowvar=False)

    rng = np.random.default_rng(0)
    sims = rng.multivariate_normal(mu, cov, size=simulations)
    port_rets = (np.exp(sims) - 1) @ weights
    losses = -port_value * port_rets

    var = np.quantile(losses, alpha)
    es = losses[losses >= var].mean()
    return var, es

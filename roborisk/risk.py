from __future__ import annotations

import csv
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from .datafeed import DB_PATH


def _load_prices(ticker: str, start_ts: int, end_ts: int) -> list[float]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT close FROM prices WHERE ticker=? AND ts_utc>=? AND ts_utc<=? ORDER BY ts_utc",
        (ticker, start_ts, end_ts),
    )
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows


def monte_carlo_var(
    portfolio_path: str,
    as_of: str = "2023-06-07",
    lookback_days: int = 60,
    simulations: int = 1000,
    alpha: float = 0.95,
) -> tuple[float, float]:
    """Return (VaR, ES) for portfolio using Monte Carlo simulation."""
    rng = np.random.default_rng(0)
    # read portfolio
    tickers: list[str] = []
    shares: list[float] = []
    with open(portfolio_path) as f:
        reader = csv.reader(f)
        for row in reader:
            tickers.append(row[0])
            shares.append(float(row[1]))
    shares_arr = np.array(shares)

    as_of_dt = datetime.strptime(as_of, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_dt = as_of_dt - timedelta(days=lookback_days)
    start_ts = int(start_dt.timestamp() * 1000)
    end_ts = int(as_of_dt.timestamp() * 1000)

    price_matrix = []
    last_prices = []
    for t in tickers:
        prices = _load_prices(t, start_ts, end_ts)
        if len(prices) < lookback_days + 1:
            raise ValueError(f"Insufficient data for {t}")
        price_matrix.append(prices)
        last_prices.append(prices[-1])

    price_matrix = np.array(price_matrix).T  # shape (days, assets)
    returns = np.diff(price_matrix, axis=0) / price_matrix[:-1]

    mean = returns.mean(axis=0)
    cov = np.cov(returns, rowvar=False)
    shocks = rng.multivariate_normal(mean, cov, size=simulations)

    last_prices = np.array(last_prices)
    pnl = (shares_arr * last_prices) * shocks
    portfolio_pnl = pnl.sum(axis=1)
    var = -np.quantile(portfolio_pnl, 1 - alpha)
    es = -portfolio_pnl[portfolio_pnl <= -var].mean()
    return float(var), float(es)

import csv
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np

DB_PATH = Path(__file__).resolve().parents[1] / "prices.db"


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


def _get_returns_and_price(ticker: str, as_of_dt: datetime, lookback_days: int):
    end_ts = int((as_of_dt + timedelta(days=1)).timestamp() * 1000)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT ts_utc, close FROM prices WHERE ticker=? AND ts_utc <= ? ORDER BY ts_utc DESC LIMIT ?",
        (ticker, end_ts, lookback_days + 1),
    )
    rows = cur.fetchall()[::-1]
    conn.close()
    if len(rows) < lookback_days + 1:
        raise ValueError(f"not enough data for {ticker}")
    closes = np.array([r[1] for r in rows], dtype=float)
    returns = np.diff(np.log(closes))
    return returns, closes[-1]


def monte_carlo_var(
    portfolio_path: str,
    as_of: str = "2023-06-07",
    lookback_days: int = 60,
    simulations: int = 1000,
    alpha: float = 0.95,
):
    as_of_dt = datetime.fromisoformat(as_of)
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

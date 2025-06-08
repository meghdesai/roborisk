import typer
from rich import print
from rich.panel import Panel
from rich.table import Table
from datetime import datetime, timedelta

from roborisk.datafeed import ingest as ingest_prices, DEFAULT_START, DEFAULT_END
from roborisk.risk import monte_carlo_var
from roborisk.explain import explain_var

app = typer.Typer(add_completion=False)


@app.command()
def ingest(
    tickers: str,
    start: str = DEFAULT_START.isoformat(),
    end: str = DEFAULT_END.isoformat(),
):
    """Ingest price data for ``tickers`` between ``start`` and ``end``."""
    tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]
    ingest_prices(tickers_list, start=start, end=end)


@app.command()
def var(portfolio: str,
        date: str = typer.Option("2023-06-07",
                                 "--date", "-d",
                                 help="Trading date YYYY-MM-DD")):
    """VAR/ES for <date> and the previous trading day."""
    d0 = datetime.fromisoformat(date)
    d1 = d0 - timedelta(days=1)

    var0, es0 = monte_carlo_var(portfolio, as_of=d0)
    var1, es1 = monte_carlo_var(portfolio, as_of=d1)

    tbl = Table(show_header=False, pad_edge=False)
    tbl.add_row("1-day VAR @ 95%", f"-${var0:,.0f}", f"(prev: -${var1:,.0f})")
    tbl.add_row("Expected Shortfall", f"-${es0:,.0f}", f"(prev: -${es1:,.0f})")
    print(Panel(tbl, title=f"RoboRisk {d0.date()}"))


@app.command()
def explain(
    portfolio: str,
    date: str = typer.Option(
        "2023-06-07", "--date", "-d", help="Date (YYYY-MM-DD) to explain VAR spike"
    ),
):
    dt_today = datetime.fromisoformat(date)
    dt_yest  = dt_today - timedelta(days=1)

    var_today, _ = monte_carlo_var(portfolio, as_of=dt_today)
    var_yest, _  = monte_carlo_var(portfolio, as_of=dt_yest)

    with open(portfolio) as f:
        drivers = [line.split(",")[0] for line in f if line.strip()]

    text = explain_var(var_today, var_yest, drivers, date)
    print(Panel(text, title=f"Why did VAR change on {date}?"))


def main():
    app()


if __name__ == "__main__":
    main()

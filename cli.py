from __future__ import annotations

import typer
from rich import print

from roborisk.datafeed import ingest as ingest_data
from roborisk.risk import monte_carlo_var
from roborisk.explain import explain_var

app = typer.Typer()


@app.command()
def ingest(tickers: str):
    tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
    ingest_data(tickers_list)
    print("[green]Ingestion complete[/green]")


@app.command()
def var(portfolio: str = typer.Option(...)):
    var_val, es = monte_carlo_var(portfolio)
    print(f"[bold]VaR:[/bold] {var_val:.2f}  [bold]ES:[/bold] {es:.2f}")


@app.command()
def explain(portfolio: str = typer.Option(...)):
    # compute var for today and yesterday
    var_today, _ = monte_carlo_var(portfolio, as_of="2023-06-07")
    var_yest, _ = monte_carlo_var(portfolio, as_of="2023-06-06")
    drivers = []
    explanation = explain_var(var_today, var_yest, drivers)
    print("[cyan]" + explanation + "[/cyan]")


if __name__ == "__main__":
    app()


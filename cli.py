import typer
from rich import print
from rich.panel import Panel

from roborisk.datafeed import ingest as ingest_prices
from roborisk.risk import monte_carlo_var
from roborisk.explain import explain_var

app = typer.Typer(add_completion=False)


@app.command()
def ingest(tickers: str):
    tickers_list = [t.strip() for t in tickers.split(',') if t.strip()]
    ingest_prices(tickers_list)


@app.command()
def var(portfolio: str):
    var_val, es = monte_carlo_var(portfolio)
    print(f"VaR: {var_val:.2f}  ES: {es:.2f}")


@app.command()
def explain(portfolio: str):
    var_today, _ = monte_carlo_var(portfolio, as_of="2023-06-07")
    var_yesterday, _ = monte_carlo_var(portfolio, as_of="2023-06-06")
    with open(portfolio) as f:
        drivers = [line.split(",")[0] for line in f if line.strip()]
    text = explain_var(var_today, var_yesterday, drivers)
    print(Panel(text))


def main():
    app()


if __name__ == "__main__":
    main()

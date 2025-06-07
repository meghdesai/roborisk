# roborisk

Quick start:

```bash
pip install -e .
export MONGODB_URI="<your mongo connection string>"
roborisk ingest --tickers AAPL,MSFT,SPY --start 2023-02-06 --end 2024-01-31
roborisk var --portfolio data/portfolio.csv
roborisk explain --portfolio data/portfolio.csv
```

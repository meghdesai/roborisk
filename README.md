# roborisk

Quick start:

```bash
pip install -e .
export MONGODB_URI="<your mongo connection string>"
roborisk ingest --tickers AAPL,MSFT,SPY
roborisk var --portfolio data/portfolio.csv
roborisk explain --portfolio data/portfolio.csv
```

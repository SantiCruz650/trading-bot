import yfinance as yf; print("yfinance works"); data = yfinance.download("AAPL", period="1d"); print(data.tail())

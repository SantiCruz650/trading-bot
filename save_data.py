import requests
import pandas as pd
import os

API_KEY = "T5WTP0VA1I2VXUGR" # Your API key
ticker = "BTC"
url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={ticker}&market=USD&apikey={API_KEY}"

response = requests.get(url)
data = response.json()

if "Time Series (Digital Currency Daily)" in data:
    ts = data["Time Series (Digital Currency Daily)"]
    df = pd.DataFrame.from_dict(ts, orient='index')
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)
    df.sort_index(inplace=True)
    df.rename(columns={'4. close': 'close', '5. volume': 'volume'}, inplace=True)
    df.to_csv(f"{ticker}_data.csv")
    print(f"Successfully saved {ticker} data to {ticker}_data.csv")
else:
    print("Could not fetch data. API limit likely reached.")

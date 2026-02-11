import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import logging
import time
from shared.price_cache import PriceCache

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, lite_mode: bool = False):
        self.cache = PriceCache()
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.lite_mode = lite_mode
        self._error_counts = {}
        self._circuit_open_until = {}

    def _is_circuit_open(self, source: str) -> bool:
        """Check if the circuit breaker is open for a specific source."""
        if source in self._circuit_open_until:
            if time.time() < self._circuit_open_until[source]:
                logger.warning(f"Circuit breaker open for {source}. Skipping request.")
                return True
            else:
                del self._circuit_open_until[source]
                self._error_counts[source] = 0  # Reset on retry
        return False

    def _record_error(self, source: str):
        """Record an error and potentially open the circuit."""
        self._error_counts[source] = self._error_counts.get(source, 0) + 1
        if self._error_counts[source] >= 3:  # Open circuit after 3 failures
            logger.error(f"Opening circuit breaker for {source} for 60 seconds.")
            self._circuit_open_until[source] = time.time() + 60

    def _fetch_alpha_vantage(self, symbol: str) -> pd.DataFrame:
        """Fetch data from Alpha Vantage (without using cache)."""
        if self._is_circuit_open("alphavantage"):
            return pd.DataFrame()

        # Optimization: Compact output size for Lite Mode if possible (AV supports full/compact)
        output_size = "compact" if self.lite_mode else "full"
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize={output_size}&apikey={self.alpha_vantage_key}"
        
        try:
            response = requests.get(url, timeout=15) # Reduced timeout for responsiveness
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data or "Time Series (Daily)" not in data:
                logger.error(f"Error fetching data for {symbol} from Alpha Vantage")
                self._record_error("alphavantage")
                return pd.DataFrame()
                
            ts = data["Time Series (Daily)"]
            df = pd.DataFrame.from_dict(ts, orient='index')
            df.index = pd.to_datetime(df.index)
            # Rename columns to match our standard
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype(float)
            df.sort_index(inplace=True)
            return df
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data: {e}")
            self._record_error("alphavantage")
            return pd.DataFrame()

    def _fetch_yfinance(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        """Fetch data from Yahoo Finance (without using cache)."""
        if self._is_circuit_open("yfinance"):
            return pd.DataFrame()

        # Optimization: Fetch less data in Lite Mode
        if self.lite_mode and period == "5y":
            period = "1y"

        try:
            data = yf.download(symbol, period=period, progress=False, auto_adjust=True)
            if not data.empty:
                # Create a new DataFrame with lowercase columns
                new_data = pd.DataFrame(index=data.index)
                
                # Map yfinance columns to our standardized names
                column_map = {
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                }
                
                # Copy data with new column names, handling both simple and multi-index
                for yf_name, our_name in column_map.items():
                    if isinstance(data.columns, pd.MultiIndex):
                        if yf_name in data.columns.get_level_values(0):
                            new_data[our_name] = data[yf_name]
                    else:
                        if yf_name in data.columns:
                            new_data[our_name] = data[yf_name]
                
                # Ensure we have all required columns
                if not all(col in new_data.columns for col in ['open', 'high', 'low', 'close', 'volume']):
                    logger.error(f"Missing required columns. Available: {new_data.columns.tolist()}")
                    return pd.DataFrame()
                
                # Remove timezone info for consistency and sort index
                new_data.index = new_data.index.tz_localize(None)
                new_data = new_data.sort_index()
                
                # Fix: Don't force frequency inference as it can fail with missing days (weekends/holidays)
                # Instead, just ensure we have enough data points
                
                # Ensure float type for all columns
                for col in new_data.columns:
                    new_data[col] = new_data[col].astype(float)
                
                return new_data
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching yfinance data: {e}")
            self._record_error("yfinance")
            return pd.DataFrame()

    def get_historical_data(self, symbol: str, source: str = "alphavantage", days: int = 365) -> pd.DataFrame:
        """
        Get historical price data, using cache when available.
        
        Args:
            symbol: The stock/crypto symbol
            source: 'alphavantage' or 'yfinance'
            days: Number of days of history to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        # Optimization: Cap days in Lite Mode
        if self.lite_mode and days > 365:
            days = 365

        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Check cache first
        df = self.cache.get_price_range(symbol, start_time, end_time, source)
        
        # If we have recent data in cache, return it
        if not df.empty and (end_time - df.index[-1]).days < 1:
            return df
            
        # Need to fetch new data
        if source == "alphavantage":
            new_df = self._fetch_alpha_vantage(symbol)
        else:  # yfinance
            # For yfinance, convert days to proper period format
            # yfinance accepts: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            if days <= 5:
                period = "5d"
            elif days <= 30:
                period = "1mo"
            elif days <= 90:
                period = "3mo"
            elif days <= 180:
                period = "6mo"
            elif days <= 365:
                period = "1y"
            elif days <= 730:
                period = "2y"
            else:
                period = "5y"
            
            new_df = self._fetch_yfinance(symbol, period=period)
            
        # If we got new data, cache it and return the requested portion
        if not new_df.empty:
            try:
                self.cache.save_prices(symbol, new_df, source)
                # Get the exact date range we want
                mask = (new_df.index >= start_time) & (new_df.index <= end_time)
                return new_df[mask]
            except Exception as e:
                logger.error(f"Error saving to cache: {e}")
                return new_df[mask]  # Still return data even if cache fails
            
        return pd.DataFrame()

    def get_latest_price(self, symbol: str, source: str = "alphavantage") -> float:
        """Get the most recent closing price for a symbol."""
        df = self.get_historical_data(symbol, source, days=5)  # Get recent data
        if not df.empty:
            return df['close'].iloc[-1]
        return None
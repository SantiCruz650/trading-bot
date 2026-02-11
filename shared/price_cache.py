import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

class PriceCache:
    def __init__(self, db_path=None):
        if db_path is None:
            # Store in the same directory as this file
            db_path = Path(__file__).parent / 'price_cache.db'
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database with the OHLCV table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ohlcv (
                    symbol TEXT,
                    source TEXT,
                    timestamp INTEGER,  -- Unix timestamp in seconds
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    fetched_at INTEGER,
                    PRIMARY KEY (symbol, source, timestamp)
                )
            """)
            # Index for range queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ohlcv_lookup 
                ON ohlcv(symbol, source, timestamp)
            """)
    
    def get_price_range(self, symbol: str, start_time: datetime, end_time: datetime, source: str = 'alphavantage'):
        """Get prices for a symbol between start and end time from cache."""
        # Convert to midnight UTC to match stored timestamps
        start_ts = int(pd.Timestamp(start_time).floor('D').timestamp())
        end_ts = int(pd.Timestamp(end_time).ceil('D').timestamp())
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                """
                SELECT timestamp, open, high, low, close, volume 
                FROM ohlcv 
                WHERE symbol = ? AND source = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
                """,
                conn,
                params=(symbol, source, start_ts, end_ts)
            )
            if not df.empty:
                # Convert to datetime with timezone info removed for consistency
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s').dt.tz_localize(None)
                df.set_index('timestamp', inplace=True)
                
                # Ensure columns are in the expected order
                df = df[['open', 'high', 'low', 'close', 'volume']]
                
                # Note: Don't force frequency as crypto/stock data has gaps (weekends/holidays)
                # Pandas will handle this automatically
            return df
    
    def save_prices(self, symbol: str, df: pd.DataFrame, source: str = 'alphavantage'):
        """Save price data to cache. DataFrame must have OHLCV columns."""
        if df.empty:
            return
            
        df = df.copy()
        
        # Convert columns to strings if they're tuples (from MultiIndex)
        if any(isinstance(col, tuple) for col in df.columns):
            df.columns = [col[-1] if isinstance(col, tuple) else col for col in df.columns]
        
        # Standardize column names to lowercase
        df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
        
        # Ensure we have the expected columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have columns: {required_cols}")
        
        # Convert to records for SQLite
        now = int(datetime.now().timestamp())
        records = []
        
        for idx, row in df.iterrows():
            # Handle both datetime and Timestamp index
            if isinstance(idx, (pd.Timestamp, datetime)):
                timestamp = int(idx.timestamp())
            else:
                timestamp = int(pd.Timestamp(idx).timestamp())
            
            # Handle NaN/None values
            record = [
                symbol,
                source,
                timestamp,
                float(row['open'] if pd.notnull(row['open']) else 0),
                float(row['high'] if pd.notnull(row['high']) else 0),
                float(row['low'] if pd.notnull(row['low']) else 0),
                float(row['close'] if pd.notnull(row['close']) else 0),
                float(row['volume'] if pd.notnull(row['volume']) else 0),
                now
            ]
            records.append(record)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO ohlcv 
                (symbol, source, timestamp, open, high, low, close, volume, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records
            )
    
    def get_last_update(self, symbol: str, source: str = 'alphavantage') -> datetime:
        """Get the timestamp of the most recent price update for a symbol."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                """
                SELECT MAX(timestamp) 
                FROM ohlcv 
                WHERE symbol = ? AND source = ?
                """,
                (symbol, source)
            ).fetchone()
            
            if result[0]:
                return datetime.fromtimestamp(result[0])
            return datetime.min
    
    def clear_old_data(self, days: int = 365):
        """Remove data older than specified days."""
        cutoff = int((datetime.now() - timedelta(days=days)).timestamp())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM ohlcv WHERE timestamp < ?", (cutoff,))
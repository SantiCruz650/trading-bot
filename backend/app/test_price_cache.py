import unittest
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path
from .price_cache import PriceCache
from .data_fetcher import DataFetcher

class TestPriceCache(unittest.TestCase):
    def setUp(self):
        # Use a test database
        self.test_db = Path(__file__).parent / 'test_cache.db'
        if self.test_db.exists():
            os.remove(self.test_db)
        self.cache = PriceCache(self.test_db)
        
    def tearDown(self):
        if self.test_db.exists():
            os.remove(self.test_db)
    
    def test_save_and_retrieve(self):
        # Create sample data with timezone-naive daily dates
        dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D', tz=None)
        df = pd.DataFrame(
            index=dates,
            data={
                'open': [100.0] * len(dates),
                'high': [110.0] * len(dates),
                'low': [90.0] * len(dates),
                'close': [105.0] * len(dates),
                'volume': [1000.0] * len(dates)
            })
        
        # Save to cache
        self.cache.save_prices('AAPL', df)
        
        # Retrieve and verify
        start = datetime(2023, 1, 1)
        end = datetime(2023, 1, 10)
        retrieved = self.cache.get_price_range('AAPL', start, end)
        
        self.assertEqual(len(df), len(retrieved))
        pd.testing.assert_frame_equal(
            df,
            retrieved,
            check_exact=False,  # Allow for small float differences
            check_names=False   # Column order may vary
        )

class TestDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = DataFetcher()
        
    def test_fetch_recent(self):
        """Test that we can fetch recent data for a major symbol."""
        symbol = 'SPY'  # More reliable test symbol
        df = self.fetcher.get_historical_data(symbol, source='yfinance', days=5)
        
        self.assertFalse(df.empty)
        self.assertTrue(all(col in df.columns for col in ['open', 'high', 'low', 'close', 'volume']))
        
        # Should be cached now - try fetching again
        df2 = self.fetcher.get_historical_data(symbol, source='yfinance', days=5)
        self.assertFalse(df2.empty)
        self.assertEqual(len(df), len(df2))  # Should get same amount of data

if __name__ == '__main__':
    unittest.main()
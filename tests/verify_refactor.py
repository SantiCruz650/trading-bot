import sys
from pathlib import Path
import os

# Add root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

def test_shared_import():
    print("Testing shared library import...")
    try:
        from shared.data_fetcher import DataFetcher
        print("✅ Successfully imported shared.data_fetcher")
        
        df = DataFetcher(lite_mode=True)
        print(f"✅ Successfully instantiated DataFetcher (Lite Mode: {df.lite_mode})")
        return True
    except Exception as e:
        print(f"❌ Failed to import shared.data_fetcher: {e}")
        return False

def test_service_imports():
    print("\nTesting service imports...")
    try:
        # Mock env vars needed for config
        os.environ["ALPHA_VANTAGE_API_KEY"] = "test"
        
        from backend.app.main import app as backend_app
        print("✅ Successfully imported backend.app.main")
        
        from ml_service.app.main import app as ml_app
        print("✅ Successfully imported ml_service.app.main")
        return True
    except Exception as e:
        print(f"❌ Failed to import services: {e}")
        return False

if __name__ == "__main__":
    if test_shared_import() and test_service_imports():
        print("\n🎉 All verification checks passed!")
        sys.exit(0)
    else:
        print("\n⚠️ Verification failed!")
        sys.exit(1)

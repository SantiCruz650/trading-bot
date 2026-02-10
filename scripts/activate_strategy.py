import sys
import os
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.append(str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import engine, Base
from app.models.models import Strategy, User

# Force absolute path to match config.py
DB_URL = "sqlite:////home/santiagomiguelcruz/trading-bot/backend/tradingbot.db"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(bind=engine)

def switch_to_eth_dca():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Get or create a default user
        user = db.query(User).first()
        if not user:
            user = User(username="default_user", hashed_password="placeholder_password")
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created default user: {user.username}")

        # 2. Deactivate existing BTC strategies
        btc_strategies = db.query(Strategy).filter(
            Strategy.ticker == "BTC",
            Strategy.status == "ACTIVE"
        ).all()
        for s in btc_strategies:
            s.status = "TERMINATED"
            print(f"Deactivated BTC strategy (ID: {s.id})")
        
        if btc_strategies:
            db.commit()

        # 3. Check if ETH strategy already exists
        existing_eth = db.query(Strategy).filter(
            Strategy.ticker == "ETH",
            Strategy.type == "DCA",
            Strategy.status == "ACTIVE"
        ).first()

        if existing_eth:
            print(f"Active DCA strategy for ETH already exists (ID: {existing_eth.id})")
            return

        # 4. Create new ETH DCA strategy
        # interval_hours=0.02 is approx 72 seconds
        new_strategy = Strategy(
            user_id=user.id,
            ticker="ETH",
            type="DCA",
            params={"amount": 2, "interval_hours": 0.02},
            status="ACTIVE"
        )
        db.add(new_strategy)
        db.commit()
        print(f"✅ Successfully activated ETH/USDT DCA strategy (5 USDT, ~36s interval)")

    except Exception as e:
        print(f"❌ Error switching strategy: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    switch_to_eth_dca()

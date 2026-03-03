from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Strategy, User
import os

DATABASE_URL = "sqlite:////home/santiagomiguelcruz/trading-bot/backend/tradingbot.db"

def seed_strategy():
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Get or create a default user
        user = db.query(User).first()
        if not user:
            print("❌ No user found in database. Please register a user first.")
            return

        # 2. Check if ETH/USDT strategy exists
        ticker = "ETH/USDT"
        existing = db.query(Strategy).filter(Strategy.ticker == ticker, Strategy.status == "ACTIVE").first()
        
        if existing:
            print(f"✅ Active strategy for {ticker} already exists (ID: {existing.id})")
            return

        # 3. Create new strategy
        new_strategy = Strategy(
            user_id=user.id,
            ticker=ticker,
            type="DCA",
            params={
                "base_order": 10.0,
                "safety_orders": 3,
                "price_deviation": 1.0,
                "tp_pct": 1.5
            },
            status="ACTIVE"
        )
        db.add(new_strategy)
        db.commit()
        print(f"🚀 Created new {new_strategy.type} strategy for {ticker} for user {user.username}")
        
    except Exception as e:
        print(f"❌ Error seeding strategy: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_strategy()

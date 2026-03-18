import sys
import os
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.models import User, Strategy, StrategyExecution, PaperTrade, LiveTrade, Prediction, Alert

def cleanup_santi():
    db = SessionLocal()
    try:
        from sqlalchemy import func
        # Search for user 'santi', 'Santi' or 'santiagomiguelcruz' case-insensitively
        target_usernames = ["santi", "santiagomiguelcruz", "Santi"]
        santi_user = db.query(User).filter(func.lower(User.username).in_([u.lower() for u in target_usernames])).first()
        
        if not santi_user:
            print(f"❓ User with names {target_usernames} not found. Skipping cleanup.")
            return

        print(f"🗑️ Cleaning up ALL data for user: {santi_user.username} (ID: {santi_user.id})")
        
        # 1. Delete Predictions
        num_preds = db.query(Prediction).filter(Prediction.owner_id == santi_user.id).delete(synchronize_session=False)
        print(f"✅ Deleted {num_preds} predictions.")

        # 2. Delete Alerts
        num_alerts = db.query(Alert).filter(Alert.owner_id == santi_user.id).delete(synchronize_session=False)
        print(f"✅ Deleted {num_alerts} alerts.")

        # 3. Delete Strategy Executions & Strategies
        strategies = db.query(Strategy).filter(Strategy.user_id == santi_user.id).all()
        strategy_ids = [s.id for s in strategies]
        
        if strategy_ids:
            num_execs = db.query(StrategyExecution).filter(StrategyExecution.strategy_id.in_(strategy_ids)).delete(synchronize_session=False)
            print(f"✅ Deleted {num_execs} strategy executions.")
            
            num_strats = db.query(Strategy).filter(Strategy.id.in_(strategy_ids)).delete(synchronize_session=False)
            print(f"✅ Deleted {num_strats} strategies.")
        
        # 4. Delete Paper Trades
        num_paper = db.query(PaperTrade).filter(PaperTrade.owner_id == santi_user.id).delete(synchronize_session=False)
        print(f"✅ Deleted {num_paper} paper trades.")
        
        # 5. Delete Live Trades
        num_live = db.query(LiveTrade).filter(LiveTrade.user_id == santi_user.id).delete(synchronize_session=False)
        print(f"✅ Deleted {num_live} live trades.")
        
        # 6. Delete User Account
        db.delete(santi_user)
        print(f"🔥 DELETED user account: {santi_user.username}")
        
        db.commit()
        print("🎉 Cleanup completed successfully. Supabase egress should stabilize.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Cleanup failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_santi()

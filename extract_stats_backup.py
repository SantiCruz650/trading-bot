import sqlite3
import json

def get_stats():
    conn = sqlite3.connect('tradingbot.db')
    cursor = conn.cursor()
    
    # Total trades
    cursor.execute("SELECT COUNT(*) FROM trades WHERE status='closed'")
    total_trades = cursor.fetchone()[0]
    
    # Total profit
    cursor.execute("SELECT SUM(profit_abs) FROM trades WHERE status='closed'")
    total_profit_abs = cursor.fetchone()[0] or 0
    
    # Avg profit pct
    cursor.execute("SELECT AVG(profit_pct) FROM trades WHERE status='closed'")
    avg_profit_pct = cursor.fetchone()[0] or 0
    
    # Max drawdown (rough estimate from balance history if available, or just min profit)
    cursor.execute("SELECT MIN(profit_abs) FROM trades WHERE status='closed'")
    max_trade_loss = cursor.fetchone()[0] or 0
    
    # Win rate
    cursor.execute("SELECT COUNT(*) FROM trades WHERE status='closed' AND profit_abs > 0")
    wins = cursor.fetchone()[0]
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # Time range
    cursor.execute("SELECT MIN(entry_time), MAX(exit_time) FROM trades WHERE status='closed'")
    start_time, end_time = cursor.fetchone()
    
    stats = {
        "total_trades": total_trades,
        "total_profit_abs": total_profit_abs,
        "avg_profit_pct": avg_profit_pct,
        "max_trade_loss": max_trade_loss,
        "win_rate": win_rate,
        "start_time": start_time,
        "end_time": end_time
    }
    
    print(json.dumps(stats, indent=2))
    conn.close()

if __name__ == "__main__":
    get_stats()

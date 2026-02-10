import sqlite3
import json

def get_stats():
    conn = sqlite3.connect('backend/tradingbot.db')
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f'Tables: {tables}')
    
    # Try to find trades or similar
    table_name = 'trades'
    if ('trades',) not in tables:
        # Check other common names
        for t in tables:
            if 'trade' in t[0].lower() or 'order' in t[0].lower() or 'cycle' in t[0].lower():
                table_name = t[0]
                break
    
    print(f'Using table: {table_name}')
    
    try:
        # Total trades
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_trades = cursor.fetchone()[0]
        
        # Total profit
        try:
            cursor.execute(f"SELECT SUM(profit_abs) FROM {table_name}")
            total_profit_abs = cursor.fetchone()[0] or 0
        except:
            total_profit_abs = 0

        # Win rate
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE profit_abs > 0")
            wins = cursor.fetchone()[0]
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        except:
            win_rate = 0
            
        stats = {
            'total_trades': total_trades,
            'total_profit_abs': total_profit_abs,
            'win_rate': win_rate,
            'table': table_name
        }
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f'Error: {e}')
    
    conn.close()

if __name__ == '__main__':
    get_stats()

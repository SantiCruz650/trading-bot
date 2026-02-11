import sqlite3
import json

def get_stats():
    conn = sqlite3.connect('backend/tradingbot.db')
    cursor = conn.cursor()
    
    # Check paper_trades schema
    cursor.execute("PRAGMA table_info(paper_trades)")
    columns = [c[1] for c in cursor.fetchall()]
    print(f'Columns in paper_trades: {columns}')
    
    # Try to calculate profit/stats
    try:
        cursor.execute("SELECT COUNT(*) FROM paper_trades")
        total_trades = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status='closed'")
        closed_trades = cursor.fetchone()[0]
        
        # If there is a profit or price column
        profit_col = 'profit' if 'profit' in columns else ('pnl' if 'pnl' in columns else None)
        
        if profit_col:
            cursor.execute(f"SELECT SUM({profit_col}) FROM paper_trades WHERE status='closed'")
            total_profit = cursor.fetchone()[0] or 0
            print(f'Total Profit ({profit_col}): {total_profit}')
        else:
            print('No profit column found. Calculating from entry/exit if available.')
            if 'entry_price' in columns and 'exit_price' in columns:
                cursor.execute("SELECT entry_price, exit_price, amount FROM paper_trades WHERE status='closed'")
                rows = cursor.fetchall()
                total_profit = sum([(r[1] - r[0]) * r[2] for r in rows if r[0] and r[1] and r[2]])
                print(f'Calculated Total Profit: {total_profit}')

        print(f'Total Trades: {total_trades}')
        print(f'Closed Trades: {closed_trades}')
        
    except Exception as e:
        print(f'Error: {e}')
    
    conn.close()

if __name__ == '__main__':
    get_stats()

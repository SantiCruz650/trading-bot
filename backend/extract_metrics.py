import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

DB_PATH = "/home/santiagomiguelcruz/trading-bot/backend/tradingbot.db"

def get_quantitative_data():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Total Days & Trades
    trades_df = pd.read_sql_query("SELECT * FROM paper_trades ORDER BY created_at", conn)
    executions_df = pd.read_sql_query("SELECT * FROM strategy_executions ORDER BY timestamp", conn)
    
    if trades_df.empty and executions_df.empty:
        return "No data found."

    # Parse dates
    trades_df['created_at'] = pd.to_datetime(trades_df['created_at'])
    if not executions_df.empty:
        executions_df['timestamp'] = pd.to_datetime(executions_df['timestamp'])

    start_date = trades_df['created_at'].min()
    end_date = trades_df['created_at'].max()
    total_days = (end_date - start_date).days + 1
    
    total_trades = len(trades_df)
    
    # 2. Winrate & Profit Factor
    sell_trades = trades_df[trades_df['type'] == 'SELL']
    wins = len(sell_trades[sell_trades['pnl'] > 0])
    winrate = (wins / len(sell_trades) * 100) if not sell_trades.empty else 0
    
    gross_profit = sell_trades[sell_trades['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
    
    # 3. Returns
    initial_balance = 1000.0 # Hypothetical initial
    total_pnl = trades_df['pnl'].sum()
    total_return_pct = (total_pnl / initial_balance) * 100
    
    # Monthly Return
    months = total_days / 30.44
    monthly_return = total_return_pct / months if months > 0 else total_return_pct
    
    # 4. Max Drawdown
    # Reconstruct equity curve
    trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
    trades_df['equity'] = initial_balance + trades_df['cumulative_pnl']
    
    peak = trades_df['equity'].cummax()
    drawdown = (peak - trades_df['equity']) / peak
    max_drawdown_pct = drawdown.max() * 100
    
    # 5. Best/Worst Day
    trades_df['date'] = trades_df['created_at'].dt.date
    daily_pnl = trades_df.groupby('date')['pnl'].sum()
    daily_return_pct = (daily_pnl / initial_balance) * 100
    
    best_day_pct = daily_return_pct.max()
    worst_day_pct = daily_return_pct.min()
    
    # 6. Avg R:R
    avg_win = sell_trades[sell_trades['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
    avg_loss = abs(sell_trades[sell_trades['pnl'] < 0]['pnl'].mean()) if (len(sell_trades) - wins) > 0 else 0
    avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
    
    # 7. Restarts & Errors (Estimated)
    # Restarts: Gaps in trading longer than 2 hours could indicate downtime or restarts
    restarts = 0
    if len(trades_df) > 1:
        diffs = trades_df['created_at'].diff()
        restarts = (diffs > timedelta(hours=2)).sum()
    
    # Errors: Check for rows with status like ERROR if available
    errors = len(trades_df[trades_df['status'].str.contains('ERROR', case=False, na=False)])
    
    # 8. Volatility periods
    # High volatility = large standard deviation of daily returns
    volatility = daily_pnl.std()
    high_vol_periods = "Si" if volatility > 50 else "No" # Arbitrary threshold
    
    # 9. Equity Curve Description
    # Check linearity
    z = np.polyfit(range(len(trades_df)), trades_df['equity'], 1)
    p = np.poly1d(z)
    residuals = trades_df['equity'] - p(range(len(trades_df)))
    variance = np.var(residuals)
    
    if variance < 500:
        equity_desc = "Lineal"
    elif max_drawdown_pct > 10:
        equity_desc = "Volátil con retrocesos"
    else:
        equity_desc = "Escalonada"

    summary = {
        "Total de días operando": total_days,
        "Número total de trades": total_trades,
        "Winrate (%)": f"{winrate:.2f}%",
        "Profit Factor": f"{profit_factor:.2f}",
        "Max Drawdown (%)": f"{max_drawdown_pct:.2f}%",
        "Retorno total (%)": f"{total_return_pct:.2f}%",
        "Retorno mensualizado": f"{monthly_return:.2f}%",
        "Promedio R:R": f"1:{avg_rr:.2f}",
        "Peor día (%)": f"{worst_day_pct:.2f}%",
        "Mejor día (%)": f"{best_day_pct:.2f}%",
        "Número de reinicios del sistema": int(restarts),
        "Número de errores de ejecución": errors,
        "Periodos de alta volatilidad": high_vol_periods,
        "Equity curve": equity_desc
    }
    
    conn.close()
    return summary

print(json.dumps(get_quantitative_data(), indent=4))

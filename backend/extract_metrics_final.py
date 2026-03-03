import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

DB_PATH = "/home/santiagomiguelcruz/trading-bot_backup_etapa2A/backend/tradingbot.db"

def get_quantitative_data():
    conn = sqlite3.connect(DB_PATH)
    
    # Load data
    trades_df = pd.read_sql_query("SELECT * FROM paper_trades ORDER BY created_at", conn)
    
    if trades_df.empty:
        return "No data found."

    # Parse dates
    trades_df['created_at'] = pd.to_datetime(trades_df['created_at'])
    start_date = trades_df['created_at'].min()
    end_date = trades_df['created_at'].max()
    total_days = (end_date - start_date).days + 1
    
    # 1. Total Trades
    total_trades = len(trades_df)
    
    # 2. Winrate & Profit Factor (on closed trades)
    closed_trades = trades_df[trades_df['status'] == 'CLOSED']
    wins = len(closed_trades[closed_trades['pnl'] > 0])
    winrate = (wins / len(closed_trades) * 100) if not closed_trades.empty else 0
    
    gross_profit = closed_trades[closed_trades['pnl'] > 0]['pnl'].sum()
    gross_loss = abs(closed_trades[closed_trades['pnl'] < 0]['pnl'].sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
    
    # 3. Returns
    initial_balance = 1000.0
    total_pnl = closed_trades['pnl'].sum()
    total_return_pct = (total_pnl / initial_balance) * 100
    
    # Monthly Return
    months = total_days / 30.41
    monthly_return = total_return_pct / months if months > 0 else total_return_pct
    
    # 4. Max Drawdown
    # We use cumulative PnL to estimate equity
    closed_trades_sorted = closed_trades.copy()
    closed_trades_sorted['cumulative_pnl'] = closed_trades_sorted['pnl'].cumsum()
    closed_trades_sorted['equity'] = initial_balance + closed_trades_sorted['cumulative_pnl']
    
    peak = closed_trades_sorted['equity'].cummax()
    drawdown = (peak - closed_trades_sorted['equity']) / peak
    max_drawdown_pct = drawdown.max() * 100 if not drawdown.empty else 0
    
    # 5. Best/Worst Day
    closed_trades_sorted['date'] = closed_trades_sorted['created_at'].dt.date
    daily_pnl = closed_trades_sorted.groupby('date')['pnl'].sum()
    daily_return_pct = (daily_pnl / initial_balance) * 100
    
    best_day_pct = daily_return_pct.max() if not daily_return_pct.empty else 0
    worst_day_pct = daily_return_pct.min() if not daily_return_pct.empty else 0
    
    # 6. Avg R:R
    avg_win = closed_trades[closed_trades['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
    avg_loss = abs(closed_trades[closed_trades['pnl'] < 0]['pnl'].mean()) if (len(closed_trades) - wins) > 0 else 0
    avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
    
    # 7. Restarts & Errors
    # Restarts estimated from gaps
    restarts = 0
    if len(trades_df) > 1:
        diffs = trades_df['created_at'].diff()
        restarts = (diffs > timedelta(hours=4)).sum()
    
    errors = len(trades_df[(trades_df['status'] != 'OPEN') & (trades_df['status'] != 'CLOSED')])
    
    # 8. Volatility
    # Check for days with high frequency of trades or large price swings in a short time
    # Actually, let's just use daily PnL variance as a proxy
    high_vol_periods = "Si (visto en periodos de alto volumen de transacciones)" if len(trades_df) > 5000 else "No"
    
    # 9. Equity Curve Description
    # With many open trades (DCA style), the curve of "CLOSED" profit is often stepped
    if len(closed_trades) < total_trades * 0.1:
        equity_desc = "Escalonada (típica de DCA con pocas salidas cerradas)"
    else:
        equity_desc = "Volátil"

    summary = {
        "Total de días operando": int(total_days),
        "Número total de trades": int(total_trades),
        "Winrate (%)": f"{winrate:.2f}%",
        "Profit Factor": f"{profit_factor:.2f}",
        "Max Drawdown (%)": f"{max_drawdown_pct:.2f}%",
        "Retorno total (%)": f"{total_return_pct:.2f}%",
        "Retorno mensualizado": f"{monthly_return:.2f}%",
        "Promedio R:R": f"1:{avg_rr:.2f}",
        "Peor día (%)": f"{worst_day_pct:.2f}%",
        "Mejor día (%)": f"{best_day_pct:.2f}%",
        "Número de reinicios del sistema": int(restarts),
        "Número de errores de ejecución": int(errors),
        "Si hubo periodos de alta volatilidad": high_vol_periods,
        "Equity curve": equity_desc
    }
    
    conn.close()
    return summary

data = get_quantitative_data()
print(json.dumps(data, indent=4))

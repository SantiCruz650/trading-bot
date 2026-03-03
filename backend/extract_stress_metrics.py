import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "/home/santiagomiguelcruz/trading-bot_backup_etapa2A/backend/tradingbot.db"

def analyze_stress():
    conn = sqlite3.connect(DB_PATH)
    execs = pd.read_sql_query("SELECT * FROM strategy_executions ORDER BY timestamp", conn)
    execs['timestamp'] = pd.to_datetime(execs['timestamp'])
    
    # 1. Movimientos adversos Fuertes
    # Reconstruct prices
    prices = execs.set_index('timestamp')['price'].resample('1min').ffill()
    prices_24h = prices.pct_change(periods=1440) # 24h rolling return
    
    moves_5 = (prices_24h.abs() > 0.05).any()
    moves_8 = (prices_24h.abs() > 0.08).any()
    moves_10 = (prices_24h.abs() > 0.10).any()
    
    max_24h_drop = prices_24h.min() * 100
    
    # Intraday volatility expansion
    vol_expansion = prices.pct_change().std() * np.sqrt(1440) # Annualized 1min vol as proxy
    
    # 2. Exposición Máxima
    # Simulation of position state
    current_asset = 0
    current_cost = 0
    max_exposure_usdt = 0
    dca_levels = 0
    max_dca_levels = 0
    
    for i, row in execs.iterrows():
        if row['order_type'] == 'BUY':
            current_asset += row['amount'] / row['price']
            current_cost += row['amount']
            dca_levels += 1
        else:
            # We assume FIFO or uniform sell for this analysis
            current_asset = 0
            current_cost = 0
            dca_levels = 0
            
        max_exposure_usdt = max(max_exposure_usdt, current_cost)
        max_dca_levels = max(max_dca_levels, dca_levels)
        
    initial_bankroll = 1000.0
    max_exposure_pct = (max_exposure_usdt / initial_bankroll) * 100
    
    # 3. System Stress
    restarts = (execs['timestamp'].diff() > timedelta(hours=4)).sum()
    
    # 4. Cumulative Risk
    # Check concurrent BUYs in different assets
    # (Since most data is ETH, we check if BTC (id 1) was ever concurrently open with ETH (id 2))
    # We'll just check if there are any overlaps in time for different strategy_ids
    
    # 5. Equity Under Pressure
    # Reconstruct equity curve with mark-to-market
    equity_curve = []
    curr_cash = 1000.0
    curr_asset = 0
    
    for i, row in execs.iterrows():
        if row['order_type'] == 'BUY':
            curr_cash -= row['amount']
            curr_asset += row['amount'] / row['price']
        else:
            curr_cash += row['amount']
            curr_asset = 0 # Simplified sell-all
            
        equity = curr_cash + (curr_asset * row['price'])
        equity_curve.append(equity)
        
    equity_series = pd.Series(equity_curve)
    peak = equity_series.cummax()
    dd = (peak - equity_series) / peak
    max_intraday_dd_pct = dd.max() * 100
    
    # Duration without new high
    duration_no_ath = 0
    if len(equity_series) > 1:
        is_ath = (equity_series == peak)
        last_ath_idx = 0
        for idx, val in enumerate(is_ath):
            if val:
                duration_no_ath = max(duration_no_ath, idx - last_ath_idx)
                last_ath_idx = idx
    
    results = {
        "max_24h_drop_pct": f"{max_24h_drop:.2f}%",
        "moves_gt_5": "Si" if moves_5 else "No",
        "moves_gt_8": "Si" if moves_8 else "No",
        "moves_gt_10": "Si" if moves_10 else "No",
        "max_dca_levels": int(max_dca_levels),
        "max_exposure_usdt": f"{max_exposure_usdt:.2f}",
        "max_exposure_pct": f"{max_exposure_pct:.2f}%",
        "restarts": int(restarts),
        "max_intraday_dd_pct": f"{max_intraday_dd_pct:.2f}%",
        "duration_no_ath_trades": int(duration_no_ath)
    }
    
    return results

print(analyze_stress())

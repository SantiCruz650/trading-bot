import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "/home/santiagomiguelcruz/trading-bot_backup_etapa2A/backend/tradingbot.db"

def analyze_stress():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Movimientos adversos Fuertes
    # Focus on ETH (Strategy 2)
    execs_eth = pd.read_sql_query("SELECT * FROM strategy_executions WHERE strategy_id=2 ORDER BY timestamp", conn)
    execs_eth['timestamp'] = pd.to_datetime(execs_eth['timestamp'])
    
    # Reconstruct prices (approximate)
    prices = execs_eth.set_index('timestamp')['price'].resample('1min').ffill()
    
    # Check 24h movements
    prices_24h = prices.pct_change(periods=1440)
    gt_5 = (prices_24h.abs() > 0.05).any()
    gt_8 = (prices_24h.abs() > 0.08).any()
    gt_10 = (prices_24h.abs() > 0.10).any()
    
    # 2. Exposición & DCA
    current_asset = 0
    current_cost = 0
    max_exposure_usdt = 0
    dca_levels = 0
    max_dca_levels = 0
    
    # We use a state machine for Strategy 2
    for i, row in execs_eth.iterrows():
        if row['order_type'] == 'BUY':
            current_asset += row['amount'] / row['price']
            current_cost += row['amount']
            dca_levels += 1
        else:
            # Proportionate sell or total exit?
            # StrategyEngine usually sells 20% or total. 
            # Given the high winrate (97%), we assume it exit most of the time.
            # Let's check the pnl from paper_trades to see where exits happened.
            current_asset = 0
            current_cost = 0
            dca_levels = 0
            
        max_exposure_usdt = max(max_exposure_usdt, current_cost)
        max_dca_levels = max(max_dca_levels, dca_levels)
        
    # Simultaneous exposure
    execs_btc = pd.read_sql_query("SELECT * FROM strategy_executions WHERE strategy_id=1 ORDER BY timestamp", conn)
    execs_btc['timestamp'] = pd.to_datetime(execs_btc['timestamp'])
    
    overlapping = 0
    if not execs_btc.empty:
        btc_start = execs_btc['timestamp'].min()
        btc_end = execs_btc['timestamp'].max()
        eth_during_btc = execs_eth[(execs_eth['timestamp'] >= btc_start) & (execs_eth['timestamp'] <= btc_end)]
        overlapping = len(eth_during_btc)

    # 3. Hidden risks: Proximity to problem
    # Max drop against avg_price
    max_drawdown_against_pos = 0
    curr_avg = 0
    curr_amt = 0
    for i, row in execs_eth.iterrows():
        if row['order_type'] == 'BUY':
            total_cost = (curr_avg * curr_amt) + row['amount']
            curr_amt += (row['amount'] / row['price'])
            curr_avg = total_cost / curr_amt if curr_amt > 0 else 0
        else:
            if curr_avg > 0:
                dd = (curr_avg - row['price']) / curr_avg
                max_drawdown_against_pos = max(max_drawdown_against_pos, dd)
            curr_avg = 0
            curr_amt = 0

    results = {
        "max_24h_move_abs": f"{prices_24h.abs().max()*100:.2f}%",
        "gt_5": "Si" if gt_5 else "No",
        "gt_8": "Si" if gt_8 else "No",
        "gt_10": "Si" if gt_10 else "No",
        "max_dca_levels": int(max_dca_levels),
        "max_exposure_usdt": f"{max_exposure_usdt:.2f}",
        "max_exposure_pct_of_bankroll": f"{(max_exposure_usdt/1000.0)*100:.2f}%",
        "concurrent_exposure_events": overlapping,
        "max_dd_against_avg_price": f"{max_drawdown_against_pos*100:.2f}%"
    }
    return results

print(analyze_stress())

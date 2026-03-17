import sqlite3
from datetime import datetime
import os
from app.core.config import settings

def generate_report(date_str=None):
    # Use absolute path from settings or hardcoded for now
    db_path = "/home/santiagomiguelcruz/trading-bot/backend/tradingbot.db"
    if not os.path.exists(db_path):
        return {"error": f"Database not found at {db_path}"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 1. Get all trades to calculate current balance and portfolio
    query = """
    SELECT s.ticker, se.order_type, se.price, se.amount, se.timestamp 
    FROM strategy_executions se
    JOIN strategies s ON se.strategy_id = s.id
    ORDER BY se.timestamp ASC
    """
    cursor.execute(query)
    all_trades = cursor.fetchall()
    
    from app.services.exchange_service import get_exchange
    exchange = get_exchange(local_simulation=settings.MOCK_EXCHANGE)
    
    initial_balance = 1000.0
    live_balance = exchange.get_balance()
    total_assets = {}
    
    # Calculate assets from all trades
    for ticker, side, price, amount, ts in all_trades:
        asset_amount = amount / price
        if side.upper() == 'BUY':
            total_assets[ticker] = total_assets.get(ticker, 0) + asset_amount
        else:
            total_assets[ticker] = total_assets.get(ticker, 0) - asset_amount
            
    # 2. Filter today's trades
    today_trades = [t for t in all_trades if t[4].startswith(date_str)]
    
    report = {
        "date": date_str,
        "total_trades_today": len(today_trades),
        "assets_traded": list(set(t[0] for t in today_trades)),
        "total_bought_today": sum(t[3] for t in today_trades if t[1].upper() == 'BUY'),
        "total_sold_today": sum(t[3] for t in today_trades if t[1].upper() == 'SELL'),
        "current_balance": live_balance,
        "balance_start_of_day": 0.0,
        "daily_cash_flow": 0.0,
        "portfolio": {},
        "total_portfolio_value": 0.0,
        "total_pnl_usdt": 0.0,
        "total_pnl_pct": 0.0,
        "daily_trades": [],
        "daily_pnl": 0.0,
        "eth_accumulated": 0.0,
        "daily_max_drawdown_pct": 0.0,
        "bot_status": "ACTIVE"
    }
    
    # Format daily trades
    for ticker, side, price, amount, ts in today_trades:
        report["daily_trades"].append({
            "ticker": ticker,
            "side": side,
            "price": price,
            "amount": amount,
            "timestamp": ts
        })
    
    # Average price for assets traded today
    for ticker in report["assets_traded"]:
        ticker_trades = [t for t in today_trades if t[0] == ticker]
        if ticker_trades:
            avg_price = sum(t[2] for t in ticker_trades) / len(ticker_trades)
            report[f"avg_price_{ticker}"] = avg_price

    # Balance at start of day
    balance_start_of_day = initial_balance
    for ticker, side, price, amount, ts in all_trades:
        if ts.startswith(date_str):
            break
        if side.upper() == 'BUY':
            balance_start_of_day -= amount
        else:
            balance_start_of_day += amount
    
    report["balance_start_of_day"] = balance_start_of_day
    report["daily_cash_flow"] = live_balance - balance_start_of_day
    
    # Portfolio Value
    total_value = live_balance
    for ticker, amount_held in total_assets.items():
        if amount_held > 0:
            # Get current price from the last trade
            last_price = [t[2] for t in all_trades if t[0] == ticker][-1]
            value = amount_held * last_price
            total_value += value
            report["portfolio"][ticker] = {
                "amount": amount_held,
                "value_usdt": value,
                "last_price": last_price
            }
            
    report["total_portfolio_value"] = total_value
    report["total_pnl_usdt"] = total_value - initial_balance
    report["total_pnl_pct"] = (report["total_pnl_usdt"] / initial_balance) * 100
    
    # 3. Advanced Metrics
    sells_query = "SELECT pnl, created_at FROM paper_trades WHERE type='SELL'"
    cursor.execute(sells_query)
    all_sell_pnls = cursor.fetchall()
    
    sell_pnls = [r[0] for r in all_sell_pnls]
    daily_sell_pnls = [r[0] for r in all_sell_pnls if r[1].startswith(date_str)]
    report["daily_pnl"] = round(sum(daily_sell_pnls), 2)
    
    win_rate = (len([p for p in sell_pnls if p > 0]) / len(sell_pnls) * 100) if sell_pnls else 0
    
    gross_profit = sum([p for p in sell_pnls if p > 0])
    gross_loss = abs(sum([p for p in sell_pnls if p < 0]))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0)
    
    # Avg time between trades
    avg_time_between_trades = 0
    if len(all_trades) > 1:
        try:
            # Handle both string and datetime objects if necessary
            def parse_ts(ts):
                if isinstance(ts, datetime): return ts
                return datetime.fromisoformat(ts.replace(' ', 'T'))
            
            timestamps = [parse_ts(t[4]) for t in all_trades]
            intervals = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
            avg_time_between_trades = sum(intervals) / len(intervals)
        except Exception:
            pass
            
    # Equity Curve & Max Drawdown
    equity_curve = []
    current_cash = initial_balance
    max_equity = initial_balance
    max_drawdown = 0
    temp_assets = {}
    
    for ticker, side, price, amount, ts in all_trades:
        asset_amount = amount / price
        if side.upper() == 'BUY':
            temp_assets[ticker] = temp_assets.get(ticker, 0) + asset_amount
            current_cash -= amount
        else:
            temp_assets[ticker] = temp_assets.get(ticker, 0) - asset_amount
            current_cash += amount
            
        # Current value of assets at this trade's price (approximation)
        assets_value = sum([amt * price for t, amt in temp_assets.items()])
        total_val = current_cash + assets_value
        equity_curve.append(round(total_val, 2))
        
        dd = (max_equity - total_val) / max_equity if max_equity > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd
            
    # Daily Max Drawdown
    daily_max_equity = balance_start_of_day
    daily_max_drawdown = 0
    temp_cash = balance_start_of_day
    temp_assets_daily = {}
    
    # We need to reconstruct the portfolio at the start of the day
    for ticker, side, price, amount, ts in all_trades:
        if ts.startswith(date_str):
            break
        asset_amount = amount / price
        if side.upper() == 'BUY':
            temp_assets_daily[ticker] = temp_assets_daily.get(ticker, 0) + asset_amount
        else:
            temp_assets_daily[ticker] = temp_assets_daily.get(ticker, 0) - asset_amount

    for ticker, side, price, amount, ts in today_trades:
        asset_amount = amount / price
        if side.upper() == 'BUY':
            temp_assets_daily[ticker] = temp_assets_daily.get(ticker, 0) + asset_amount
            temp_cash -= amount
        else:
            temp_assets_daily[ticker] = temp_assets_daily.get(ticker, 0) - asset_amount
            temp_cash += amount
            
        assets_val = sum([amt * price for t, amt in temp_assets_daily.items()])
        total_v = temp_cash + assets_val
        if total_v > daily_max_equity:
            daily_max_equity = total_v
        d_dd = (daily_max_equity - total_v) / daily_max_equity if daily_max_equity > 0 else 0
        if d_dd > daily_max_drawdown:
            daily_max_drawdown = d_dd
    
    report["daily_max_drawdown_pct"] = round(daily_max_drawdown * 100, 2)

    # Total Cycles & Bot Status
    import json
    cursor.execute("SELECT status, params FROM strategies")
    strategies_data = cursor.fetchall()
    total_cycles = 0
    is_paused = False
    now = datetime.utcnow()
    
    for status, p in strategies_data:
        if status == "PAUSED":
            is_paused = True
        if p:
            try:
                params_dict = json.loads(p)
                total_cycles += params_dict.get("total_cycles", 0)
                paused_until = params_dict.get("paused_until")
                if paused_until and now < datetime.fromisoformat(paused_until):
                    is_paused = True
            except: pass

    report.update({
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "total_cycles": total_cycles,
        "win_rate_pct": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_time_between_trades_sec": round(avg_time_between_trades, 2),
        "equity_curve": equity_curve[-20:], # Last 20 points
        "eth_accumulated": round(total_assets.get("ETH", 0.0), 6),
        "bot_status": "PAUSED" if is_paused else "ACTIVE"
    })
    
    conn.close()
    return report

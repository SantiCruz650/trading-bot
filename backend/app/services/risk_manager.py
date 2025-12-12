import math

class RiskManager:
    def __init__(self, bankroll: float = 10000.0):
        self.bankroll = bankroll
        self.max_risk_per_trade = 0.05 # Never risk more than 5% of bankroll

    def calculate_kelly_bet(self, win_prob: float, win_loss_ratio: float = 2.0) -> float:
        """
        Calculate optimal bet size using Kelly Criterion.
        f* = (bp - q) / b
        where:
        f* = fraction of bankroll to wager
        b = odds received on the wager (win_loss_ratio)
        p = probability of winning
        q = probability of losing (1 - p)
        """
        if win_prob <= 0.5:
            return 0.0
            
        q = 1.0 - win_prob
        f_star = ((win_loss_ratio * win_prob) - q) / win_loss_ratio
        
        # Half-Kelly is safer for real trading to avoid ruin
        safe_kelly = f_star * 0.5
        
        # Cap at max risk
        return max(0.0, min(safe_kelly, self.max_risk_per_trade))

    def get_position_size(self, confidence: str, current_price: float) -> float:
        """
        Determine position size based on ML confidence.
        """
        # Map confidence to probability (simplified)
        if confidence == "HIGH":
            win_prob = 0.65
        elif confidence == "MEDIUM":
            win_prob = 0.55
        else:
            win_prob = 0.50
            
        kelly_fraction = self.calculate_kelly_bet(win_prob)
        position_value = self.bankroll * kelly_fraction
        
        return position_value / current_price

    def calculate_sl_tp(self, entry_price: float, side: str, risk_reward_ratio: float = 2.0) -> tuple:
        """
        Calculate Stop Loss and Take Profit levels.
        Default strategy: 1:2 Risk/Reward with dynamic stop loss based on volatility (simulated here as fixed %)
        """
        # In a real app, this would use ATR (Average True Range) for dynamic stops
        stop_loss_pct = 0.02 # 2% default stop loss
        
        if side.upper() == 'BUY':
            stop_loss = entry_price * (1 - stop_loss_pct)
            take_profit = entry_price * (1 + (stop_loss_pct * risk_reward_ratio))
        else: # SELL
            stop_loss = entry_price * (1 + stop_loss_pct)
            take_profit = entry_price * (1 - (stop_loss_pct * risk_reward_ratio))
            
        return stop_loss, take_profit

    # --- Methods for Live Trading Support ---
    
    @property
    def circuit_breaker_active(self):
        return False # Simple stub

    @property
    def circuit_breaker_reason(self):
        return None

    def can_trade(self, current_balance: float) -> tuple:
        """Check if trading is allowed based on risk rules"""
        if current_balance < 10.0:
            return False, "Insufficient balance"
        return True, "OK"

    def calculate_position_size(self, balance: float, price: float) -> tuple:
        """Calculate safe position size"""
        # Risk 2% of balance
        risk_amount = balance * 0.02
        # Assuming stop loss is 2%, then position size = risk_amount / 0.02 = balance
        # But let's be conservative: 10% of balance per trade
        position_value = balance * 0.10
        amount = position_value / price
        return position_value, amount

    def record_trade(self, value: float, is_opening: bool):
        """Record trade for stats (stub)"""
        pass

    def get_daily_stats(self):
        """Get daily risk stats (stub)"""
        return {
            "trades": 0,
            "pnl": 0.0,
            "exposure": 0.0
        }

    def reset_circuit_breaker(self):
        """Reset circuit breaker (stub)"""
        pass

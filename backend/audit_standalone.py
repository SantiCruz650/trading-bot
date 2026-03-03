
import sys
import os
import math
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# STANDALONE RISK MANAGER LOGIC (Copied from app/services/risk_manager.py)
class RiskManager:
    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.max_risk_per_trade = 0.05
        self._gec_state = "NORMAL"
        self._freeze_active = False
        self._freeze_reason = None
        self._kill_switch_active = False
        self._daily_start_time = datetime.utcnow().date()
        self._daily_start_equity = bankroll
        self._daily_peak_equity = bankroll
        self._current_equity = bankroll
        self._total_position_value = 0.0
        self._consecutive_losses = 0
        
        # Hardcoded setttings for audit
        class MockSettings:
            ETAPA_2A_ACTIVE = True
            GEC_SOFT_CAP = 0.65
            GEC_HARD_CAP = 0.80
            FREEZE_DD_THRESHOLD = 0.015
            KILL_SWITCH_DD_THRESHOLD = 0.030
            KILL_SWITCH_ER_THRESHOLD = 0.95
            KILL_SWITCH_CONSECUTIVE_LOSSES = 5
        self.settings = MockSettings()

    def update_equity(self, current_balance: float, total_position_value: float):
        self._current_equity = current_balance + total_position_value
        self._total_position_value = total_position_value
        if self._current_equity > self._daily_peak_equity:
            self._daily_peak_equity = self._current_equity
            
    def calculate_exposure_ratio(self) -> float:
        if self._current_equity <= 0: return 0.0
        return self._total_position_value / self._current_equity
    
    def calculate_daily_drawdown(self) -> float:
        if self._daily_peak_equity <= 0: return 0.0
        return (self._daily_peak_equity - self._current_equity) / self._daily_peak_equity
    
    def update_gec_state(self):
        er = self.calculate_exposure_ratio()
        dd = self.calculate_daily_drawdown()
        if dd > self.settings.KILL_SWITCH_DD_THRESHOLD or er > self.settings.KILL_SWITCH_ER_THRESHOLD:
            self._gec_state = "KILL_SWITCH"
            self._kill_switch_active = True
        elif er >= self.settings.GEC_HARD_CAP:
            self._gec_state = "HARD_CAP"
        elif er >= self.settings.GEC_SOFT_CAP:
            self._gec_state = "SOFT_CAP"
        else:
            self._gec_state = "NORMAL"
    
    def can_open_position(self, side: str = "BUY") -> tuple:
        if self._kill_switch_active: return False, "Kill-Switch"
        if self._gec_state == "HARD_CAP" and side.upper() == "BUY":
            return False, "Hard Cap"
        return True, "OK"

class AuditExchange:
    def __init__(self, initial_balance=1000.0, fee_pct=0.001):
        self.virtual_balance = initial_balance
        self.fee_pct = fee_pct
        self.price = 2500.0
        self.position = 0.0
        self.orders = []

    def place_market_order(self, side, amount):
        usdt_value = amount * self.price
        fee = usdt_value * self.fee_pct
        if side == 'buy':
            if usdt_value + fee > self.virtual_balance: return None
            self.virtual_balance -= (usdt_value + fee)
            self.position += amount
        else:
            self.virtual_balance += (usdt_value - fee)
            self.position -= amount
        return {'price': self.price, 'fee': fee}

def run_audit():
    print("🔬 AUDIT: CRASH -20% | FEES 0.1% | MAX DCA 20")
    print("-" * 50)
    
    bankroll = 1000.0
    rm = RiskManager(bankroll=bankroll)
    ex = AuditExchange(initial_balance=bankroll, fee_pct=0.001)
    
    # -20% Crash Price Path
    prices = np.linspace(2500, 2000, 200)
    
    equity_curve = []
    gec_blocks = 0
    dca_levels = 0
    max_er = 0
    
    for p in prices:
        ex.price = p
        
        # Mark to Market
        pos_value = ex.position * p
        rm.update_equity(ex.virtual_balance, pos_value)
        rm.update_gec_state()
        
        er = rm.calculate_exposure_ratio()
        max_er = max(max_er, er)
        
        # Try to DCA if under limit
        if dca_levels < 20: 
            can_buy, reason = rm.can_open_position("BUY")
            if not can_buy:
                gec_blocks += 1
            else:
                # Buy 50 USDT worth (stress)
                amount = 50.0 / p
                if ex.place_market_order('buy', amount):
                    dca_levels += 1
        
        equity = ex.virtual_balance + (ex.position * p)
        equity_curve.append(equity)
        if equity <= 0: break

    equity_series = pd.Series(equity_curve)
    max_dd = ((equity_series.cummax() - equity_series) / equity_series.cummax()).max() * 100
    
    print(f"--- RESULTADOS ---")
    print(f"Capital Final: {equity_series.iloc[-1]:.2f} USDT")
    print(f"Max Exposure Ratio: {max_er:.4f}")
    print(f"Max Drawdown: {max_dd:.2f}%")
    print(f"DCA Levels reached: {dca_levels}")
    print(f"GEC Hard Cap Blocks: {gec_blocks}")
    print(f"Survival: {'SI' if equity_series.iloc[-1] > 0 else 'NO (INSOLVENCIA)'}")
    
    risk = "CRÍTICO" if equity_series.iloc[-1] < 500 or max_dd > 30 else ("ALTO" if max_dd > 15 else "MEDIO")
    print(f"NIVEL DE RIESGO: {risk}")

if __name__ == "__main__":
    run_audit()

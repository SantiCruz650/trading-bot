
import sys
import os
import math
from datetime import datetime

# STANDALONE RISK MANAGER LOGIC (Hardcoded for audit)
class RiskManager:
    def __init__(self, bankroll: float = 1000.0):
        self.bankroll = bankroll
        self.settings_active = True
        self.soft_cap = 0.65
        self.hard_cap = 0.80
        self.kill_switch_dd = 0.030
        self.kill_switch_er = 0.95
        
        self._current_equity = bankroll
        self._total_pos_value = 0.0
        self._peak_equity = bankroll
        self._gec_state = "NORMAL"
        self._kill_switch = False

    def update_state(self, balance, pos_value):
        self._current_equity = balance + pos_value
        self._total_pos_value = pos_value
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity
        
        er = self._total_pos_value / self._current_equity if self._current_equity > 0 else 0
        dd = (self._peak_equity - self._current_equity) / self._peak_equity if self._peak_equity > 0 else 0
        
        if dd > self.kill_switch_dd or er > self.kill_switch_er:
            self._gec_state = "KILL_SWITCH"
            self._kill_switch = True
        elif er >= self.hard_cap:
            self._gec_state = "HARD_CAP"
        elif er >= self.soft_cap:
            self._gec_state = "SOFT_CAP"
        else:
            self._gec_state = "NORMAL"

    def can_buy(self):
        if self._kill_switch: return False
        if self._gec_state == "HARD_CAP": return False
        return True

def run_audit():
    print("🔬 AUDIT: CRASH -20% | FEES 0.1% | MAX DCA 20")
    sys.stdout.flush()
    
    initial_bankroll = 1000.0
    balance = initial_bankroll
    position = 0.0
    rm = RiskManager(initial_bankroll)
    
    # Generate -20% path manually (200 steps)
    start_p = 2500.0
    end_p = 2000.0
    prices = [start_p - (i * (start_p - end_p) / 199) for i in range(200)]
    
    max_er = 0
    dca_levels = 0
    gec_blocks = 0
    equity_curve = []
    
    for p in prices:
        # Mark to market
        pos_value = position * p
        rm.update_state(balance, pos_value)
        
        er = pos_value / (balance + pos_value) if (balance + pos_value) > 0 else 0
        max_er = max(max_er, er)
        
        # Strategy intent: Buy 50 USDT every level up to 20
        if dca_levels < 20:
            if not rm.can_buy():
                gec_blocks += 1
            else:
                cost = 50.0
                fee = cost * 0.001
                if balance >= cost + fee:
                    balance -= (cost + fee)
                    position += (cost / p)
                    dca_levels += 1
        
        equity = balance + (position * p)
        equity_curve.append(equity)
        if equity <= 0: break

    final_equity = equity_curve[-1]
    peak_equity = max(equity_curve)
    max_dd = ((peak_equity - min(equity_curve)) / peak_equity) * 100
    
    print("-" * 50)
    print(f"Capital Final: {final_equity:.2f} USDT")
    print(f"Exposición Máxima (ER): {max_er:.4f}")
    print(f"Drawdown Máximo Real: {max_dd:.2f}%")
    print(f"Niveles DCA ejecutados: {dca_levels}")
    print(f"Bloqueos GEC Hard Cap: {gec_blocks}")
    print(f"Resultado: {'SUPERVIVENCIA' if final_equity > 0 else 'INSOLVENCIA'}")
    
    risk_level = "CRÍTICO" if final_equity < 500 or max_dd > 25 else "ALTO"
    print(f"NIVEL DE RIESGO: {risk_level}")
    sys.stdout.flush()

if __name__ == "__main__":
    run_audit()

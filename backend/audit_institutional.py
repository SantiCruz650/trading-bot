
import sys
import math
import random

class InstitutionalRiskManager:
    def __init__(self, bk):
        self.bk = bk
        self.eq = bk
        self.pos_val = 0.0
        self.peak = bk
        self.gec = 'NORMAL'
        self.ks = False
        # Institutional Settings
        self.soft_cap = 0.20
        self.hard_cap = 0.30
        self.kill_switch_dd = 0.030
        self.kill_switch_er = 0.95

    def update(self, bal, pv):
        self.eq = bal + pv
        self.pos_val = pv
        if self.eq > self.peak: self.peak = self.eq
        er = pv / self.eq if self.eq > 0 else 0
        dd = (self.peak - self.eq) / self.peak if self.peak > 0 else 0
        
        if dd > self.kill_switch_dd or er > self.kill_switch_er:
            self.gec = 'KILL_SWITCH'; self.ks = True
        elif er >= self.hard_cap:
            self.gec = 'HARD_CAP'
        elif er >= self.soft_cap:
            self.gec = 'SOFT_CAP'
        else:
            self.gec = 'NORMAL'

    def can_buy(self):
        return not self.ks and self.gec != 'HARD_CAP'

def run_simulation(name, prices, initial_bk=1000.0, dca_amount=50.0):
    print(f"\n--- 🔬 {name} ---")
    bal = initial_bk
    pos = 0.0
    rm = InstitutionalRiskManager(initial_bk)
    max_er = 0
    dca_levels = 0
    gec_blocks = 0
    curve = []
    
    for p in prices:
        pv = pos * p
        rm.update(bal, pv)
        er = pv / (bal + pv) if (bal + pv) > 0 else 0
        max_er = max(max_er, er)
        
        # DCA Logic (Cap 20)
        if dca_levels < 20:
            if not rm.can_buy():
                gec_blocks += 1
            else:
                cost = dca_amount
                fee = cost * 0.001
                if bal >= cost + fee:
                    bal -= (cost + fee)
                    pos += (cost / p)
                    dca_levels += 1
        
        curve.append(bal + pos * p)
        if (bal + pos * p) <= 0: break

    final = curve[-1]
    mdd = ((max(curve) - min(curve)) / max(curve)) * 100
    surv = 'SI' if final > 0 else 'NO'
    
    print(f"Capital Final: {final:.2f} USDT")
    print(f"Max Exposure (ER): {max_er:.4f}")
    print(f"Max Drawdown: {mdd:.2f}%")
    print(f"DCA Levels: {dca_levels} / 20")
    print(f"GEC Blocks: {gec_blocks}")
    print(f"Survival: {surv}")
    
    risk = "CRÍTICO" if final < 700 or mdd > 30 else ("ALTO" if mdd > 15 else "MEDIO")
    return {"final": final, "mdd": mdd, "max_er": max_er, "risk": risk}

if __name__ == "__main__":
    # 1. Crash -20%
    crash_prices = [2500 - (i * 500 / 199) for i in range(200)]
    run_simulation("CRASH -20% SIMULATION", crash_prices)
    
    # 2. Bearish Trend -25% in 48h
    # 2880 steps (1 step per min approx)
    bear_prices = [2500 - (i * 625 / 2879) for i in range(2880)]
    # Add 3x noise
    bear_prices_noisy = [p * (1 + (random.random() - 0.5) * 0.0006) for p in bear_prices]
    res = run_simulation("BEARISH TREND -25% (48h)", bear_prices_noisy)
    
    print("\n" + "="*50)
    verdict = "READY WITH MODERATE RISK" if res["risk"] != "CRÍTICO" else "NOT READY"
    print(f"INSTITUTIONAL VERDICT: {verdict}")
    print("="*50)

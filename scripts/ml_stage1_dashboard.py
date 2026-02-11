import json
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class Stage1Dashboard:
    def __init__(self, log_path="/home/santiagomiguelcruz/trading-bot/data/ml_evaluation_extended.json"):
        self.log_path = log_path

    def load_data(self):
        if not os.path.exists(self.log_path):
            return None
        with open(self.log_path, "r") as f:
            return json.load(f)["sessions"]

    def generate_report(self):
        events = self.load_data()
        if not events:
            print("❌ No hay datos suficientes para generar el reporte de la Etapa 1.")
            return

        df = pd.DataFrame(events)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # --- 1. MÉTRICAS DIARIAS ---
        print("\n" + "═"*60)
        print("📊 DASHBOARD ETAPA 1: CONSOLIDACIÓN DEFENSIVA DEL ML")
        print("═"*60)

        # A. Riesgo (Últimas 24h)
        last_24h = df[df['timestamp'] > (datetime.utcnow() - timedelta(days=1))]
        
        if not last_24h.empty:
            max_dd_24h = last_24h['drawdown'].max() * 100
            avg_dca_levels = last_24h['dca_levels'].mean()
            
            print(f"\n[RIESGO - ÚLTIMAS 24H]")
            status_dd = "✅ OK" if max_dd_24h <= 1.5 else "⚠️ ALERTA" if max_dd_24h <= 2.0 else "🚨 CRÍTICO"
            print(f"• Drawdown Máximo: {max_dd_24h:.2f}% ({status_dd})")
            print(f"• Niveles DCA Promedio: {avg_dca_levels:.1f}")
        else:
            print("\n[RIESGO] Sin datos en las últimas 24h.")

        # B. Comportamiento ML
        total_buys = len(df[df['original_signal'] == 'BUY'])
        blocked_buys = len(df[df['action_taken'] == 'BLOCKED_BY_ML'])
        block_rate = (blocked_buys / total_buys * 100) if total_buys > 0 else 0
        
        status_br = "✅ OK" if 15 <= block_rate <= 40 else "⚠️ IRRELEVANTE" if block_rate < 15 else "⚠️ RESTRICTIVO"
        print(f"\n[COMPORTAMIENTO ML]")
        print(f"• Tasa de Bloqueo: {block_rate:.1f}% ({status_br})")
        print(f"• Bloqueos Totales: {blocked_buys} de {total_buys} señales BUY")

        # C. Detección de Regímenes
        regime_counts = df['regime'].value_counts()
        print(f"\n[DISTRIBUCIÓN DE REGÍMENES]")
        for regime, count in regime_counts.items():
            print(f"• {regime}: {count} eventos")

        # --- 2. SEÑALES DE ALERTA (STOP CONDITIONS) ---
        print("\n" + "─"*60)
        print("🛑 STOP CONDITIONS CHECK")
        print("─"*60)
        
        alerts = []
        if not last_24h.empty and max_dd_24h > 2.0:
            alerts.append("🔴 Drawdown diario > 2% detectado.")
        if block_rate > 50:
            alerts.append("🟠 ML excesivamente restrictivo (>50% bloqueos).")
        if block_rate < 10:
            alerts.append("🟠 ML irrelevante (<10% bloqueos).")
            
        if not alerts:
            print("✅ No se han disparado condiciones de parada.")
        else:
            for alert in alerts:
                print(alert)

        print("\n" + "═"*60)
        print("Regla de Oro: El ML debe perder menos y liberar capital antes.")
        print("═"*60)

if __name__ == "__main__":
    dashboard = Stage1Dashboard()
    dashboard.generate_report()

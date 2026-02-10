import sqlite3
import json
from datetime import datetime

db_path = "tradingbot.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

today = "2026-01-09"

print(f"--- Datos para {today} ---")

# 1. Trades ejecutados hoy (PaperTrade)
cursor.execute("SELECT * FROM paper_trades WHERE created_at >= ?", (today,))
paper_trades = cursor.fetchall()
print(f"\nPaper Trades ({len(paper_trades)}):")
for t in paper_trades:
    print(t)

# 2. Ejecuciones de estrategia hoy
cursor.execute("SELECT * FROM strategy_executions WHERE timestamp >= ?", (today,))
strategy_executions = cursor.fetchall()
print(f"\nStrategy Executions ({len(strategy_executions)}):")
for e in strategy_executions:
    print(e)

# 3. Predicciones de ML hoy
cursor.execute("SELECT * FROM predictions WHERE created_at >= ?", (today,))
predictions = cursor.fetchall()
print(f"\nPredictions ({len(predictions)}):")
for p in predictions:
    print(p)

# 4. Estrategias activas y sus parámetros
cursor.execute("SELECT * FROM strategies")
strategies = cursor.fetchall()
print(f"\nStrategies:")
for s in strategies:
    print(s)

# 5. Live Trades (por si acaso)
cursor.execute("SELECT * FROM live_trades WHERE created_at >= ?", (today,))
live_trades = cursor.fetchall()
print(f"\nLive Trades ({len(live_trades)}):")
for lt in live_trades:
    print(lt)

conn.close()

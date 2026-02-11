import sqlite3
conn = sqlite3.connect('backend/tradingbot.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM paper_trades ORDER BY created_at DESC LIMIT 5")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()

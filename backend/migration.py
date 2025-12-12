from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import models

DATABASE_URL = "sqlite:///./tradingbot.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
session = SessionLocal()

def upgrade():
    print("Starting migration: Changing 'predicted_close' to TEXT for SQLite...")
    with engine.connect() as connection:
        # Use text() to execute raw SQL
        connection.execute(text("ALTER TABLE predictions RENAME TO _predictions_old;"))
        connection.execute(text("CREATE TABLE predictions (id INTEGER PRIMARY KEY, ticker TEXT, last_close REAL, signal TEXT, created_at DATETIME, owner_id INTEGER);"))
        connection.execute(text("INSERT INTO predictions (id, ticker, last_close, signal, created_at, owner_id) SELECT id, ticker, last_close, signal, created_at, owner_id FROM _predictions_old;"))
        connection.execute(text("DROP TABLE _predictions_old;"))
    print("Migration complete: 'predicted_close' is now TEXT.")

if __name__ == "__main__":
    upgrade()

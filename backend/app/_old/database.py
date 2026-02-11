from sqlalchemy import create_engine
DATABASE_URL = f"sqlite:////home/santiagomigiguelcruz/trading-bot/tradingbot.db"
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# This creates an absolute path to the database file, no matter where you run the command from.
# It will be created in the same directory as this file (backend/app).
BASE_DIR = Path(__file__).resolve().parent
SQLALCHEMY_DATABASE_URL = f"sqlite:///{BASE_DIR}/tradingbot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
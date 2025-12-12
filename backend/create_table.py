import sqlite3
from app.models import Prediction
from sqlalchemy import create_engine

# Create engine
engine = create_engine('sqlite:///trading_bot.db')

# Create the table
Prediction.__table__.create(engine)
print('Table created successfully.')

# Commit and close
print('Database updated.')
print('All done!')

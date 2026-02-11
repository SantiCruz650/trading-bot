#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/home/santiagomiguelcruz/trading-bot:/home/santiagomiguelcruz/trading-bot/ml_service:/home/santiagomiguelcruz/trading-bot/backend
export PYTHONUNBUFFERED=1
export ML_SERVICE_URL=http://localhost:8001

echo "Starting ML Service..."
cd /home/santiagomiguelcruz/trading-bot/ml_service
/home/santiagomiguelcruz/trading-bot/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > /home/santiagomiguelcruz/trading-bot/ml_service_new.log 2>&1 &
echo $! > /home/santiagomiguelcruz/trading-bot/.ml.pid

sleep 5

echo "Starting Backend..."
cd /home/santiagomiguelcruz/trading-bot/backend
/home/santiagomiguelcruz/trading-bot/venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /home/santiagomiguelcruz/trading-bot/backend.log 2>&1 &
echo $! > /home/santiagomiguelcruz/trading-bot/.backend.pid

echo "Services started."

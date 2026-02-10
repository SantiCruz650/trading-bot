#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Kill any existing services
pkill -f "uvicorn.*8000"
pkill -f "uvicorn.*8001"

# Start Redis
echo "Starting Redis..."
redis-server --daemonize yes
echo "Redis started."

# Start Backend
echo "Starting Backend Service..."
cd backend
# Try to activate venv, if not found create it
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Start Celery Worker
# echo "Starting Celery Worker..."
# celery -A app.worker worker --loglevel=info --logfile=../logs/celery.log --detach
# echo "Celery Worker started."

uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../logs/uvicorn.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../.backend.pid
echo "Backend started on port 8000 (PID: $BACKEND_PID)"

# Start ML Service
echo "Starting ML Service..."
cd ../ml_service
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

uvicorn app.main:app --host 0.0.0.0 --port 8001 > ../logs/ml_service.log 2>&1 &
ML_PID=$!
echo $ML_PID > ../.ml.pid
echo "ML Service started on port 8001 (PID: $ML_PID)"

echo "Services started. Access frontend at http://localhost:8000"

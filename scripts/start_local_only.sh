#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."
# Start backend
echo "Starting Backend..."
cd backend
source venv/bin/activate || { python3 -m venv venv && source venv/bin/activate; }
pip install -r requirements.txt > /dev/null 2>&1
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start ML service
echo "Starting ML Service..."
cd ../ml_service
source venv/bin/activate || { python3 -m venv venv && source venv/bin/activate; }
pip install -r requirements.txt > /dev/null 2>&1
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
ML_PID=$!

echo "Services started. Backend: $BACKEND_PID, ML: $ML_PID"
echo "Waiting for services to be ready..."

# Wait for ports
wait_for_port() {
    local port=$1
    local retries=30
    while ! nc -z localhost $port && [ $retries -gt 0 ]; do
        sleep 1
        ((retries--))
    done
    if [ $retries -eq 0 ]; then
        echo "Timed out waiting for port $port"
        return 1
    fi
    return 0
}

wait_for_port 8000 || exit 1
wait_for_port 8001 || exit 1

echo "All services ready!"
echo "Backend/Frontend: http://localhost:8000"
echo "ML Service: http://localhost:8001"

# Keep script running
wait

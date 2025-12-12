#!/bin/bash

echo "Restarting MCrypto services..."

# Stop existing services
pkill -f uvicorn
pkill -f http.server

# Start ML Service in background
cd ~/trading-bot/ml_service
source venv/bin/activate
export ALPHA_VANTAGE_API_KEY=1FWLCPVCME066H6M
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > ml_service.log 2>&1 &
echo "MCrypto ML Service started on port 8001"

# Start Backend in background
cd ~/trading-bot/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
echo "MCrypto Backend started on port 8000"

# Start Frontend in background
cd ~/trading-bot/frontend
nohup python3 -m http.server 8080 > frontend.log 2>&1 &
echo "MCrypto Frontend started on port 8080"

echo "All MCrypto services restarted successfully!"
echo "Access the trading dashboard at http://localhost:8080"
echo "Use password 'MCrypto2024' to access the dashboard"

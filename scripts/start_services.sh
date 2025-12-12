#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Kill any existing services
pkill -f "uvicorn.*8000"
pkill -f "uvicorn.*8001"
pkill -f "http-server.*8080"

# Start services in background
echo "Starting Backend Service..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
echo "Backend started on port 8000"

echo "Starting ML Service..."
cd ../ml_service
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
echo "ML Service started on port 8001"

echo "Starting Frontend Service..."
cd ../frontend
npx http-server -p 8080 &
echo "Frontend started on port 8080"

# Start ngrok
echo "Starting ngrok tunnels..."
ngrok start --all
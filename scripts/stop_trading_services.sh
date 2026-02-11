#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Stop ngrok
if [ -f .ngrok.pid ]; then
    kill $(cat .ngrok.pid) 2>/dev/null
    rm .ngrok.pid
fi

# Stop frontend
if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi

# Stop backend
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi

# Stop ML service
if [ -f .ml.pid ]; then
    kill $(cat .ml.pid) 2>/dev/null
    rm .ml.pid
fi

# Additional cleanup
pkill -f "python3 -m http.server 8080"
pkill -f "uvicorn.*:app"
pkill -9 ngrok

# Wait for processes to die
sleep 2

# Force kill any remaining processes on our ports
for port in 8080 8000 8001 4040; do
    pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        echo "Force killing process on port $port"
        kill -9 $pid 2>/dev/null
    fi
done

echo "All services stopped!"
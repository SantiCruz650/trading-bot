#!/bin/bash

# Start Redis in the background
redis-server --daemonize yes

# Wait a moment for Redis to start
sleep 2

# Debug: List directories to verify structure
echo "Current directory: $(pwd)"
echo "Listing /app:"
ls -F /app
echo "Listing /app/frontend:"
ls -F /app/frontend || echo "Frontend dir not found"
echo "Listing /app/backend:"
ls -F /app/backend

# ML Service is now fused directly into the Backend (Python Import)
# No need to start it as a separate process on 8001
# echo "Starting ML Service on port 8001..."
# export PYTHONPATH=$PYTHONPATH:/app:/app/ml_service
# python3 -m uvicorn ml_service.app.main:app --host 0.0.0.0 --port 8001 > /app/ml_service.log 2>&1 &
# 
# # Wait for ML service to be ready
# # echo "Waiting for ML service health check..."
# # sleep 5
echo "ML Service Integrated (Python Import)."

# Start the application (Backend)
# We use the PORT environment variable provided by Render for the backend
echo "Starting Backend on port $PORT..."
export PYTHONPATH=$PYTHONPATH:/app/backend
gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

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

# Start the application
# We use the PORT environment variable provided by Render
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

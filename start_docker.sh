#!/bin/bash

# Start Redis in the background
redis-server --daemonize yes

# Wait a moment for Redis to start
sleep 2

# Start the application
# We use the PORT environment variable provided by Render
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT

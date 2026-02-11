#!/bin/bash

# Single-tunnel ngrok starter with path-based routing
# - Creates a tunnel for the frontend (8080)
# - Backend and ML service will be accessed through URL path prefixes (/api and /ml)
# - Requires configuring reverse proxy in the backend to forward requests appropriately

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
NGROK_LOG="$PROJECT_DIR/ngrok.log"

# Kill any existing ngrok processes
if pgrep -x ngrok >/dev/null 2>&1; then
    echo "Killing existing ngrok processes..."
    pkill ngrok || true
    sleep 1
fi

# Start ngrok for frontend and capture its PID
echo "Starting ngrok tunnel for frontend..."
ngrok http 8080 > "$NGROK_LOG" 2>&1 &
NGROK_PID=$!

# Wait for the URL to be available
echo "Waiting for ngrok URL (up to 30 seconds)..."
FRONTEND_URL=""
for i in {1..30}; do
    sleep 1
    if FRONTEND_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*'); then
        break
    fi
done

if [ -z "$FRONTEND_URL" ]; then
    echo "Failed to get ngrok URL after 30 seconds. Check $NGROK_LOG for details."
    exit 1
fi

# Write URLs to configuration
cat > "$PROJECT_DIR/ngrok_urls.json" << EOF
{
    "frontend": "$FRONTEND_URL",
    "backend": "$FRONTEND_URL/api",
    "ml_service": "$FRONTEND_URL/ml"
}
EOF

echo "Ngrok URLs:"
echo "Frontend:  $FRONTEND_URL"
echo "Backend:   $FRONTEND_URL/api"
echo "ML:        $FRONTEND_URL/ml"
echo ""
echo "Next steps to enable ngrok access:"
echo "1. Update backend CORS to allow origin: $FRONTEND_URL"
echo "2. Configure reverse proxy in backend to forward paths:"
echo "   /api/* -> http://localhost:8000/*"
echo "   /ml/*  -> http://localhost:8001/*"
echo "3. Update frontend API endpoints to use ngrok URLs from ngrok_urls.json"
echo ""
echo "ngrok process is running (PID: $NGROK_PID)"
echo "View ngrok status at: http://localhost:4040"
echo "Stop ngrok with: kill $NGROK_PID"

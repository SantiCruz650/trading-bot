#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use"
        pid=$(lsof -Pi :$1 -sTCP:LISTEN -t)
        read -p "Do you want to kill the process using port $1? (y/n) " yn
        case $yn in
            [Yy]* ) kill $pid; sleep 2; return 0;;
            * ) return 1;;
        esac
    fi
    return 0
}

# Function to wait for a port to be ready
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

# Function to get ngrok URLs and save them
get_ngrok_urls() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        TUNNELS=$(curl -s http://localhost:4040/api/tunnels)
        BASE_URL=$(echo "$TUNNELS" | python3 -c "import sys, json; tunnels = json.load(sys.stdin).get('tunnels', []); print(tunnels[0]['public_url'] if tunnels else '')")
        
        if [ -n "$BASE_URL" ]; then
            FRONTEND_URL=${BASE_URL%/}
            BACKEND_URL="$FRONTEND_URL"
            ML_URL="$FRONTEND_URL"
            break
        fi
        
        echo "Waiting for ngrok tunnel (attempt $attempt/$max_attempts)..."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    cat > data/ngrok_urls.json << EOL
{
    "frontend_url": "${FRONTEND_URL}",
    "backend_url": "${BACKEND_URL}/api",
    "ml_url": "${ML_URL}/api/ml"
}
EOL
    
    echo "Ngrok URLs have been saved to data/ngrok_urls.json"
    cat data/ngrok_urls.json
}

# Kill any existing ngrok processes
pkill ngrok

# Create directory for ngrok config if it doesn't exist
mkdir -p ~/.config/ngrok

# Create ngrok.yml config file
cat > ~/.config/ngrok/ngrok.yml << EOF
version: "2"
authtoken: $NGROK_AUTH_TOKEN
tunnels:
  frontend:
    addr: 8080
    proto: http
  backend:
    addr: 8000
    proto: http
  ml:
    addr: 8001
    proto: http
EOF

# Check ports before starting
check_port 8000 || exit 1
check_port 8001 || exit 1
check_port 4040 || exit 1

# Start ngrok tunnel exposing backend (which now serves frontend + API)
(ngrok http 8000 > logs/ngrok.log 2>&1) &
NGROK_PID=$!

# Wait for ngrok to initialize and verify it's running
for i in {1..30}; do
    if curl -s http://localhost:4040/api/tunnels > /dev/null; then
        echo "Ngrok started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Failed to start ngrok"
        exit 1
    fi
    sleep 1
done

# Start backend server (also serves frontend assets)
cd backend
source $(pwd)/venv/bin/activate || { python3 -m venv venv && source venv/bin/activate; }
pip install -r requirements.txt >/dev/null 2>&1
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
wait_for_port 8000 || { echo "Backend failed to start"; exit 1; }

# Start ML service
cd ../ml_service
source $(pwd)/venv/bin/activate || { python3 -m venv venv && source venv/bin/activate; }
pip install -r requirements.txt >/dev/null 2>&1
uvicorn app.main:app --host 0.0.0.0 --port 8001 &
ML_PID=$!

# Wait for ML service to start
wait_for_port 8001 || { echo "ML service failed to start"; exit 1; }

# Save PIDs for cleanup
echo $NGROK_PID > .ngrok.pid
echo $BACKEND_PID > .backend.pid
echo $ML_PID > .ml.pid

# Get and save ngrok URLs
get_ngrok_urls
echo "All services started!"
echo "Check ngrok tunnels at http://localhost:4040"
echo "Use ./scripts/stop_trading_services.sh to stop all services"
echo "Ngrok URLs have been saved to data/ngrok_urls.json"
#!/bin/bash

# Ensure we are in the project root
cd "$(dirname "$0")/.."

# Check if services are running
check_service() {
    local port=$1
    nc -z localhost $port > /dev/null 2>&1
    return $?
}

# Ensure all services are running
echo "Checking if required services are running..."

if ! check_service 8080; then
    echo "Error: Frontend service (port 8080) is not running"
    exit 1
fi

if ! check_service 8000; then
    echo "Error: Backend service (port 8000) is not running"
    exit 1
fi

if ! check_service 8001; then
    echo "Error: ML service (port 8001) is not running"
    exit 1
fi

echo "All services are running!"
echo "Starting ngrok tunnels..."

# Clean up any existing ngrok processes
pkill ngrok

# Create a directory for ngrok logs
mkdir -p logs/ngrok

# Start tunnels
echo "Starting Frontend tunnel (8080)..."
ngrok http 8080 > logs/ngrok/frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2
echo "Starting Backend tunnel (8000)..."
ngrok http 8000 > logs/ngrok/backend.log 2>&1 &
BACKEND_PID=$!

sleep 2
echo "Starting ML Service tunnel (8001)..."
ngrok http 8001 > logs/ngrok/ml_service.log 2>&1 &
ML_PID=$!

# Function to get tunnel URL
get_tunnel_url() {
    local port=$1
    local api_port=$2
    local retries=0
    local max_retries=10
    
    while [ $retries -lt $max_retries ]; do
        local url=$(curl -s http://localhost:$api_port/api/tunnels | grep -o '"public_url":"[^"]*"' | cut -d'"' -f4)
        if [ ! -z "$url" ]; then
            echo $url
            return 0
        fi
        sleep 1
        ((retries++))
    done
    return 1
}

# Wait for tunnels to start and get URLs
sleep 5
FRONTEND_URL=$(get_tunnel_url 8080 4040)
BACKEND_URL=$(get_tunnel_url 8000 4041)
ML_URL=$(get_tunnel_url 8001 4042)

# Save URLs to configuration
cat > data/ngrok_urls.json << EOF
{
    "frontend": "${FRONTEND_URL:-"Failed to start"}",
    "backend": "${BACKEND_URL:-"Failed to start"}",
    "ml_service": "${ML_URL:-"Failed to start"}"
}
EOF

# Show URLs
echo "----------------------------------------"
echo "Ngrok Tunnel URLs:"
echo "Frontend:   ${FRONTEND_URL:-"Failed to start"}"
echo "Backend:    ${BACKEND_URL:-"Failed to start"}"
echo "ML Service: ${ML_URL:-"Failed to start"}"
echo "----------------------------------------"
echo "URLs have been saved to data/ngrok_urls.json"
echo "Tunnel logs are in logs/ngrok directory"
echo ""
echo "To stop all tunnels, run: pkill ngrok"
echo "To view tunnel logs:"
echo "  tail -f logs/ngrok/frontend.log"
echo "  tail -f logs/ngrok/backend.log"
echo "  tail -f logs/ngrok/ml_service.log"
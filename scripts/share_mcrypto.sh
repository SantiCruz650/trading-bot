#!/bin/bash

# Check if ngrok is configured
check_ngrok_auth() {
    if ! [ -f ~/.config/ngrok/ngrok.yml ]; then
        echo "Ngrok authentication not found!"
        echo "Please visit: https://dashboard.ngrok.com/get-started/your-authtoken"
        echo "Copy your authtoken and paste it here:"
        read -r authtoken
        
        if [ -z "$authtoken" ]; then
            echo "No authtoken provided. Cannot continue."
            exit 1
        fi
        
        # Configure ngrok
        echo "version: 2" > ~/.config/ngrok/ngrok.yml
        echo "authtoken: $authtoken" >> ~/.config/ngrok/ngrok.yml
        echo "web_addr: localhost:4040" >> ~/.config/ngrok/ngrok.yml
        
        echo "Ngrok configured successfully!"
    fi
}

# Run the auth check
check_ngrok_auth

# Function to check if a port is in use
check_port() {
    if lsof -i :$1 >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check if ports are in use
echo "Checking services..."

# Try multiple ways to check ports
check_services() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1 || \
       netstat -tln 2>/dev/null | grep -q ":$port\\b" || \
       ss -tln | grep -q ":$port\\b"; then
        echo "✓ $service is running on port $port"
        return 0
    else
        echo "✗ $service (port $port) is not running!"
        echo "Please start it first:"
        echo "$3"
        return 1
    fi
}

# Check each service
services_running=true

if ! check_services 8000 "Backend" "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000"; then
    services_running=false
fi

if ! check_services 8001 "ML Service" "cd ml_service && uvicorn app.main:app --host 0.0.0.0 --port 8001"; then
    services_running=false
fi

if ! check_services 8080 "Frontend" "cd frontend && python3 -m http.server 8080"; then
    services_running=false
fi

if [ "$services_running" = false ]; then
    exit 1
fi

echo "All services are running! Starting ngrok tunnels..."

# Kill any existing ngrok processes
pkill ngrok >/dev/null 2>&1

# Start ngrok tunnels
echo "Starting ngrok tunnels..."

# Function to start ngrok and get URL
start_ngrok() {
    local port=$1
    local service=$2
    local retries=0
    local max_retries=3
    
    echo "Starting tunnel for $service on port $port..."
    
    while [ $retries -lt $max_retries ]; do
        # Start ngrok and capture its output directly
        url=$(ngrok http $port --log=stdout 2>&1 | grep -o 'https://.*\.ngrok-free\.app' | head -n1)
        
        if [ ! -z "$url" ]; then
            echo "✓ $service tunnel ready: $url"
            eval "${service}_URL=\"$url\""
            return 0
        fi
        
        retries=$((retries + 1))
        echo "Retry $retries of $max_retries..."
        sleep 1
    done
    
    echo "✗ Failed to start tunnel for $service"
    return 1
}

# Kill any existing ngrok processes and wait a moment
pkill ngrok
sleep 2

# Start each tunnel in sequence
echo "Starting tunnels..."

FRONTEND_URL=$(ngrok http 8080 --log=stdout 2>&1 | grep -o 'https://.*\.ngrok-free\.app' | head -n1 &)
sleep 2
BACKEND_URL=$(ngrok http 8000 --log=stdout 2>&1 | grep -o 'https://.*\.ngrok-free\.app' | head -n1 &)
sleep 2
ML_URL=$(ngrok http 8001 --log=stdout 2>&1 | grep -o 'https://.*\.ngrok-free\.app' | head -n1 &)

# Give tunnels time to establish
echo "Waiting for tunnels to be ready..."
sleep 5

# Check the ngrok web interface for tunnel status
TUNNELS=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://.*\.ngrok-free\.app' || true)

if [ ! -z "$TUNNELS" ]; then
    FRONTEND_URL=$(echo "$TUNNELS" | head -n1)
    BACKEND_URL=$(echo "$TUNNELS" | sed -n '2p')
    ML_URL=$(echo "$TUNNELS" | sed -n '3p')
fi

# Verify we got all URLs
if [ -z "$FRONTEND_URL" ] || [ -z "$BACKEND_URL" ] || [ -z "$ML_URL" ]; then
    echo "Error: Could not get all ngrok URLs."
    echo "Frontend URL: $FRONTEND_URL"
    echo "Backend URL: $BACKEND_URL"
    echo "ML URL: $ML_URL"
    echo "Check ngrok_*.log files for errors"
    exit 1
fi

# Update the frontend configuration
echo "Updating frontend configuration..."
./update_urls.sh "$FRONTEND_URL" "$BACKEND_URL" "$ML_URL"

# Display success message and instructions
echo ""
echo "=== MCrypto Sharing Ready! ==="
echo "Share this URL with your friend: $FRONTEND_URL"
echo ""
echo "Instructions for your friend:"
echo "1. Open the URL in their browser"
echo "2. Enter the splash password: MCrypto2024"
echo "3. Create an account or login"
echo "4. Start using MCrypto!"
echo ""
echo "The app will be available as long as this computer is running."
echo "To stop sharing, just run: pkill ngrok"
echo ""
echo "Logs are available in:"
echo "- Frontend: ngrok_frontend.log"
echo "- Backend: ngrok_backend.log"
echo "- ML Service: ngrok_ml.log"
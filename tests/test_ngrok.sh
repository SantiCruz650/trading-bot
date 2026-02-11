#!/bin/bash

echo "Testing ngrok setup..."

# Kill any existing ngrok processes
pkill ngrok
sleep 2

# Try to start a single tunnel
echo "Starting test tunnel on port 8080..."
ngrok http 8080 --log=stdout > ngrok_test.log 2>&1 &

# Wait a moment for the tunnel to establish
sleep 5

# Try to get the URL
if url=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://.*\.ngrok-free\.app' | head -n1); then
    echo "Success! Tunnel created: $url"
    echo "Your ngrok configuration is working correctly."
else
    echo "Failed to create tunnel. Debugging information:"
    echo "1. Checking ngrok configuration..."
    cat ~/.config/ngrok/ngrok.yml || echo "No config file found"
    echo ""
    echo "2. Recent ngrok logs:"
    tail -n 20 ngrok_test.log
fi

# Cleanup
pkill ngrok
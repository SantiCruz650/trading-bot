#!/bin/bash

# Headless Trading Bot Startup Script

echo "🚀 Starting Trading Bot in Headless Paper Trading Mode..."

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found. Please create one based on .env.example"
    exit 1
fi

# Ensure docker compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "❌ Error: docker-compose or docker compose is not installed."
    exit 1
fi

# Start services
echo "📦 Starting containers (Backend + ML Service)..."
$DOCKER_COMPOSE -f docker-compose.headless.yml up -d --build

# Wait for backend to be ready
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Check status
docker ps --filter "name=trading-bot"

echo "✅ Bot is running!"
echo "📝 Follow logs with: $DOCKER_COMPOSE -f docker-compose.headless.yml logs -f backend"

# Display initial logs
$DOCKER_COMPOSE -f docker-compose.headless.yml logs --tail=20 backend

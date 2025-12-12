#!/bin/bash
# Trading Bot - Quick Testing Guide
# Run this script to verify all components are working

echo "======================================"
echo "TRADING BOT - SYSTEM VERIFICATION"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
echo "1️⃣  CHECKING SERVICES..."
echo ""

# ML Service
if curl -s http://localhost:8001/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} ML Service running on port 8001"
else
    echo -e "${RED}✗${NC} ML Service NOT running on port 8001"
fi

# Backend
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend running on port 8000"
else
    echo -e "${RED}✗${NC} Backend NOT running on port 8000"
fi

# Frontend
if curl -s http://localhost:8080/index.html > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend running on port 8080"
else
    echo -e "${RED}✗${NC} Frontend NOT running on port 8080"
fi

echo ""
echo "2️⃣  CHECKING MODELS..."
echo ""

# Check models
MODELS_DIR="/home/santiagomiguelcruz/trading-bot/ml_service/models"
for ticker in BTC ETH ADA SOL DOGE; do
    if [ -f "$MODELS_DIR/${ticker}_model.pkl" ] && [ -f "$MODELS_DIR/${ticker}_encoder.pkl" ]; then
        echo -e "${GREEN}✓${NC} ${ticker}: Model + Encoder loaded"
    else
        echo -e "${RED}✗${NC} ${ticker}: Missing model or encoder"
    fi
done

echo ""
echo "3️⃣  TESTING API ENDPOINTS..."
echo ""

# Test ML Service predict endpoint
echo "Testing ML Service /predict/BTC:"
RESPONSE=$(curl -s http://localhost:8001/predict/BTC)
if echo "$RESPONSE" | grep -q "signal"; then
    SIGNAL=$(echo "$RESPONSE" | grep -o '"signal":"[^"]*"')
    echo -e "${GREEN}✓${NC} Prediction working: $SIGNAL"
else
    echo -e "${YELLOW}⚠${NC} Response: $RESPONSE"
fi

echo ""
echo "Testing Backend authentication:"
AUTH=$(curl -s -X POST "http://localhost:8000/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"testuser_$(date +%s)\",\"password\":\"testpass123\"}")
if echo "$AUTH" | grep -q "username"; then
    echo -e "${GREEN}✓${NC} User registration working"
else
    echo -e "${RED}✗${NC} Registration failed: $AUTH"
fi

echo ""
echo "4️⃣  ACCURACY METRICS (Latest Backtest)..."
echo ""

# Get accuracy for each ticker
for ticker in BTC ETH ADA SOL DOGE; do
    ACCURACY=$(curl -s "http://localhost:8001/backtest/$ticker?days=100" 2>/dev/null | grep -o '"accuracy":[0-9.]*' | cut -d':' -f2)
    if [ -z "$ACCURACY" ]; then
        ACCURACY="N/A (API rate limit)"
    else
        ACCURACY="${ACCURACY}0%"
    fi
    echo -e "${YELLOW}${ticker}:${NC} $ACCURACY"
done

echo ""
echo "======================================"
echo "5️⃣  QUICK START COMMANDS"
echo "======================================"
echo ""
echo "Start ML Service:"
echo "  cd /home/santiagomiguelcruz/trading-bot/ml_service"
echo "  ALPHA_VANTAGE_API_KEY=1FWLCPVCME066H6M \\
  /home/santiagomiguelcruz/trading-bot/backtester_venv/bin/python -m uvicorn app.main:app --port 8001"
echo ""
echo "Start Backend:"
echo "  cd /home/santiagomiguelcruz/trading-bot/backend"
echo "  ALPHA_VANTAGE_API_KEY=1FWLCPVCME066H6M \\
  /home/santiagomiguelcruz/trading-bot/backtester_venv/bin/python -m uvicorn app.main:app --port 8000"
echo ""
echo "Start Frontend:"
echo "  cd /home/santiagomiguelcruz/trading-bot/frontend"
echo "  python3 -m http.server 8080"
echo ""
echo "======================================"
echo "📊 TEST IN BROWSER"
echo "======================================"
echo ""
echo "Frontend: http://localhost:8080"
echo "Backend API: http://localhost:8000/docs"
echo "ML Service: http://localhost:8001/docs"
echo ""
echo "======================================"

#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

TICKERS=("BTC" "ETH" "ADA" "SOL" "DOGE")
BASE_URL="http://localhost:8000/api/predictions/predict"

# Get token first
echo "Getting auth token..."
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test_manual&password=testpass123")

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    # Try registering if login fails
    echo "Login failed, trying to register..."
    TIMESTAMP=$(date +%s)
    curl -s -X POST "http://localhost:8000/api/auth/register" \
      -H "Content-Type: application/json" \
      -d '{"username":"test_'$TIMESTAMP'","password":"testpass123"}' > /dev/null
    
    TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/token" \
      -H "Content-Type: application/x-www-form-urlencoded" \
      -d "username=test_$TIMESTAMP&password=testpass123")
    TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
fi

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to get token${NC}"
    exit 1
fi

echo "Token obtained."
echo "Testing tickers..."

for ticker in "${TICKERS[@]}"; do
    echo -n "Testing $ticker... "
    RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/response_body "$BASE_URL/$ticker" -H "Authorization: Bearer $TOKEN" -X POST)
    HTTP_CODE=${RESPONSE: -3}
    BODY=$(cat /tmp/response_body)
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo -e "${GREEN}OK${NC}"
        echo "  Response: $BODY"
    else
        echo -e "${RED}FAILED ($HTTP_CODE)${NC}"
        echo "  Response: $BODY"
    fi
    echo "-----------------------------------"
done

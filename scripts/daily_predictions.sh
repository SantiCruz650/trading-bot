#!/bin/bash

# Get a fresh token
TOKEN=$(curl -s -X POST "http://localhost:8000/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=testuser&password=testpass" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['access_token'])
except:
    print('Error getting token')
")

# Get BTC prediction
echo "Getting BTC prediction..."
BTC_PREDICTION=$(curl -s -X POST "http://localhost:8000/predict/BTC" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"{data['ticker']} {data['signal']} {data['last_close']}\")
except:
    print('Error getting BTC prediction')
")

# Get ETH prediction
echo "Getting ETH prediction..."
ETH_PREDICTION=$(curl -s -X POST "http://localhost:8000/predict/ETH" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"{data['ticker']} {data['signal']} {data['last_close']}\")
except:
    print('Error getting ETH prediction')
")

# Log predictions
if [[ $BTC_PREDICTION == Error* ]]; then
    echo "Failed to get BTC prediction"
else
    python3 track_predictions.py log $(echo $BTC_PREDICTION) "Would follow"
fi

if [[ $ETH_PREDICTION == Error* ]]; then
    echo "Failed to get ETH prediction"
else
    python3 track_predictions.py log $(echo $ETH_PREDICTION) "Would follow"
fi

# Show dashboard
python3 crypto_dashboard.py

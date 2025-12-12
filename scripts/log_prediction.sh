#!/bin/bash

# Get the latest prediction from the backend
LATEST_PREDICTION=$(curl -s -X GET "http://localhost:8000/my-predictions" -H "Authorization: Bearer $1" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data and len(data) > 0:
        latest = data[0]
        print(f\"{latest['ticker']} {latest['signal']} {latest['last_close']}\")
    else:
        print('No predictions found')
except:
    print('Error parsing prediction data')
")

# Parse the prediction
TICKER=$(echo $LATEST_PREDICTION | cut -d' ' -f1)
SIGNAL=$(echo $LATEST_PREDICTION | cut -d' ' -f2)
PRICE=$(echo $LATEST_PREDICTION | cut -d' ' -f3)

# Log the prediction
if [ ! -z "$TICKER" ] && [ ! -z "$SIGNAL" ] && [ ! -z "$PRICE" ]; then
    python3 track_predictions.py log $TICKER $SIGNAL $PRICE "Would follow"
    echo "Logged prediction: $TICKER $SIGNAL at $PRICE"
else
    echo "Failed to parse prediction: $LATEST_PREDICTION"
fi

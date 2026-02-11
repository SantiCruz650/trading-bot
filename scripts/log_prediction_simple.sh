#!/bin/bash

echo "Enter ticker (e.g., BTC):"
read TICKER

echo "Enter signal (BUY/SELL/HOLD):"
read SIGNAL

echo "Enter price:"
read PRICE

python3 track_predictions.py log $TICKER $SIGNAL $PRICE "Would follow"
echo "Logged prediction: $TICKER $SIGNAL at $PRICE"

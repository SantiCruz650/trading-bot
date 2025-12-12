#!/bin/bash

# Check if URLs are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <frontend-url> <backend-url> <ml-service-url>"
    echo "Example: $0 https://1234.ngrok-free.app https://5678.ngrok-free.app https://9012.ngrok-free.app"
    exit 1
fi

FRONTEND_URL=$1
BACKEND_URL=$2
ML_SERVICE_URL=$3

# Create a temporary file
TMP_FILE=$(mktemp)

# Update script.js with new URLs
sed "s|const API_URL = 'http://localhost:8000'|const API_URL = '$BACKEND_URL'|g" frontend/script.js > $TMP_FILE
sed -i "s|const ML_API_URL = 'http://localhost:8001'|const ML_API_URL = '$ML_SERVICE_URL'|g" $TMP_FILE

# Backup original script
cp frontend/script.js frontend/script.js.backup

# Move temporary file to final location
mv $TMP_FILE frontend/script.js
chmod 644 frontend/script.js

echo "Updated frontend/script.js with new URLs:"
echo "Frontend: $FRONTEND_URL"
echo "Backend: $BACKEND_URL"
echo "ML Service: $ML_SERVICE_URL"
echo "Original file backed up to frontend/script.js.backup"
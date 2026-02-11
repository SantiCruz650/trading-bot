#!/bin/bash

# Function to extract ngrok URL from log file
extract_ngrok_url() {
    local log_file=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        # Try to find the URL using different patterns
        local url=$(cat $log_file | grep -o 'url=https://[^[:space:]]*' | sed 's/url=//' | tail -n1)
        
        if [ -z "$url" ]; then
            url=$(cat $log_file | grep -o 'https://[^[:space:]]*.ngrok-free.app' | tail -n1)
        fi
        
        if [ -z "$url" ]; then
            url=$(cat $log_file | grep -o 'https://[^[:space:]]*.ngrok.io' | tail -n1)
        fi
        
        if [ -n "$url" ]; then
            echo "$url"
            return 0
        fi
        
        sleep 1
        attempt=$((attempt + 1))
    done
    
    return 1
}
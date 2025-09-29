#!/bin/bash
# Script to kill all processes running on lib_url_to_img project ports

echo "🔍 Checking for processes on project ports..."

PORTS=(3000 5000 5005)

for port in "${PORTS[@]}"; do
    echo "Checking port $port..."
    PIDS=$(lsof -ti:$port 2>/dev/null)
    
    if [ -n "$PIDS" ]; then
        echo "Found processes on port $port: $PIDS"
        echo "$PIDS" | xargs -r kill -9
        echo "✅ Killed processes on port $port"
    else
        echo "✅ Port $port is free"
    fi
done

echo "🎯 All project ports checked and cleaned!" 
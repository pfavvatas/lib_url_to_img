#!/bin/bash
# Script to check and kill processes using project ports

echo "🔍 Checking for processes using project ports..."

PORTS=(3000 5000 5005)

for port in "${PORTS[@]}"; do
    echo "Checking port $port..."
    
    # Find processes using the port
    if command -v lsof &> /dev/null; then
        PIDS=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo "⚠️  Found processes using port $port: $PIDS"
            echo "🛑 Killing processes..."
            echo $PIDS | xargs kill -9
            echo "✅ Killed processes on port $port"
        else
            echo "✅ Port $port is free"
        fi
    else
        echo "⚠️  lsof not available, cannot check port $port"
    fi
done

echo "🎯 Port check complete!"

echo ""
echo "🚀 Starting the application..."
echo "=============================="

# Run the main script
./run.sh 
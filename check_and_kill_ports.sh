#!/bin/bash

echo "🔍 Checking for existing processes on required ports..."

# Function to check and kill process on a port
check_and_kill_port() {
    local port=$1
    local process_id=$(lsof -ti:$port)
    
    if [ ! -z "$process_id" ]; then
        echo "⚠️  Found process running on port $port (PID: $process_id)"
        echo "🛑 Killing process..."
        kill -9 $process_id
        echo "✅ Process killed"
    else
        echo "✅ No process running on port $port"
    fi
}

# Check and kill processes on required ports
check_and_kill_port 3000  # React frontend
check_and_kill_port 5000  # Python API
check_and_kill_port 3001  # Node server

echo ""
echo "🚀 Starting the application..."
echo "=============================="

# Run the main script
./run.sh 
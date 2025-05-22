#!/bin/bash

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "simple_bridge_server_fixed.py|ollama_service.py"
sleep 2

# Check if port 8765 is still in use
if lsof -i:8765 &>/dev/null; then
    echo "Port 8765 is still in use. Killing process..."
    lsof -ti:8765 | xargs kill -9
    sleep 1
fi

# Create necessary directories
mkdir -p logs pids

# Start the bridge server
echo "Starting bridge server..."
python3 simple_bridge_server_fixed.py > logs/bridge_server.log 2>&1 &
echo $! > pids/bridge_server.pid
sleep 2

# Check if bridge server started correctly
if [ -f pids/bridge_server.pid ] && ps -p $(cat pids/bridge_server.pid) > /dev/null; then
    echo "✅ Bridge server started successfully"
else
    echo "❌ Bridge server failed to start"
    cat logs/bridge_server.log
    exit 1
fi

# Start the Ollama service
echo "Starting Ollama LLM service..."
python3 ollama_service.py > logs/ollama_service.log 2>&1 &
echo $! > pids/ollama_service.pid
sleep 2

# Check if Ollama service started correctly
if [ -f pids/ollama_service.pid ] && ps -p $(cat pids/ollama_service.pid) > /dev/null; then
    echo "✅ Ollama service started successfully"
else
    echo "❌ Ollama service failed to start"
    cat logs/ollama_service.log
    exit 1
fi

echo "System restarted successfully!"
echo ""
echo "Testing connection to bridge server..."
echo ""
echo "Running test script..."
python3 test_bridge_connection.py
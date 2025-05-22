#!/bin/bash

# Start the complete compatibility system with Ollama LLM integration
echo "Starting compatibility chat system with Ollama LLM integration..."

# Create necessary directories
mkdir -p logs/llm
mkdir -p pids

# Check if Ollama is running
curl -s http://localhost:11434/api/version > /dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Ollama is not running. Please start Ollama before running this script."
    exit 1
fi

# Stop any existing processes
if [ -f "pids/bridge_server.pid" ]; then
    PID=$(cat "pids/bridge_server.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping existing bridge server (PID: $PID)..."
        kill $PID
        sleep 1
    fi
    rm "pids/bridge_server.pid"
fi

if [ -f "pids/ollama_service.pid" ]; then
    PID=$(cat "pids/ollama_service.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping existing Ollama service (PID: $PID)..."
        kill $PID
        sleep 1
    fi
    rm "pids/ollama_service.pid"
fi

if [ -f "pids/http_server.pid" ]; then
    PID=$(cat "pids/http_server.pid")
    if ps -p $PID > /dev/null; then
        echo "Stopping existing HTTP server (PID: $PID)..."
        kill $PID
        sleep 1
    fi
    rm "pids/http_server.pid"
fi

# Start the compatibility bridge server
echo "Starting compatibility bridge server..."
python3 compatibility_bridge_server.py > logs/compatibility_bridge.log 2>&1 &
echo $! > pids/bridge_server.pid
sleep 2

# Start the compatibility Ollama service
echo "Starting compatibility Ollama LLM service..."
python3 compatibility_ollama_service.py > logs/llm/compatibility_ollama_service.log 2>&1 &
echo $! > pids/ollama_service.pid
sleep 2

# Start the HTTP server
echo "Starting HTTP server for overlay..."
cd overlay
python3 -m http.server 8080 > ../logs/http_server.log 2>&1 &
echo $! > ../pids/http_server.pid
cd ..
sleep 1

# Open the browser with the overlay
echo "Opening overlay in browser..."
open http://localhost:8080/

echo ""
echo "Compatibility chat system is now running!"
echo "You can use the Enhanced Chat component with Ollama LLM support."
echo "The chat should now be able to respond to your messages using the Ollama model."
echo "To stop the system, run: ./stop_compatibility_chat.sh"
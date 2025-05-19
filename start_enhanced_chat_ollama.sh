#!/bin/bash

# Start the entire enhanced chat system with Ollama LLM integration
echo "Starting enhanced chat system with Ollama LLM integration..."

# Create necessary directories
mkdir -p logs/llm
mkdir -p pids

# Check if Ollama is running
curl -s http://localhost:11434/api/version > /dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Ollama is not running. Please start Ollama before running this script."
    exit 1
fi

# Start the bridge server if not already running
if ! ps aux | grep -q "[f]ixed_bridge_server.py"; then
    echo "Starting bridge server..."
    nohup python3 fixed_bridge_server.py > logs/fixed_bridge.log 2>&1 &
    echo $! > pids/bridge_server.pid
    sleep 2
fi

# Start the Ollama service if not already running
if ! ps aux | grep -q "[o]llama_service.py"; then
    echo "Starting Ollama LLM service..."
    nohup python3 ollama_service.py > logs/llm/ollama_service.log 2>&1 &
    echo $! > pids/ollama_service.pid
    sleep 2
fi

# Start the HTTP server if not already running
if ! ps aux | grep -q "[h]ttp.server 8080"; then
    echo "Starting HTTP server for overlay..."
    cd overlay
    nohup python3 -m http.server 8080 > ../logs/http_server.log 2>&1 &
    echo $! > ../pids/http_server.pid
    cd ..
    sleep 1
fi

# Open the browser with the overlay
echo "Opening overlay in browser..."
open http://localhost:8080/

echo ""
echo "Enhanced chat system is now running!"
echo "You can use the Enhanced Chat component with Ollama LLM support."
echo "The chat should now be able to respond to your messages using the Ollama model."
echo "To stop the system, run: ./stop_enhanced_chat_ollama.sh"
#!/bin/bash

# Run Agent-Based LLM WebSocket Server
# This script starts the agent-based WebSocket server that connects to Ollama LLM with memory

# Ensure directories exist
mkdir -p logs
mkdir -p pids

# Kill any existing process using port 8765
echo "Checking for existing process on port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true

# Kill existing server if running by PID
if [ -f "pids/agent_based_llm_ws.pid" ]; then
    PID=$(cat pids/agent_based_llm_ws.pid)
    if ps -p $PID > /dev/null; then
        echo "Killing existing agent-based server process: $PID"
        kill -9 $PID
    fi
    rm pids/agent_based_llm_ws.pid
fi

echo "Starting agent-based LLM WebSocket server..."
# Start the server
python3 agent_based_llm_ws.py &

# Save the PID
echo $! > pids/agent_based_llm_ws.pid
echo "Server started with PID: $(cat pids/agent_based_llm_ws.pid)"
echo "WebSocket server running on ws://localhost:8765"
echo "To monitor logs: tail -f logs/agent_based_llm_ws.log"
echo "To stop the server: pkill -F pids/agent_based_llm_ws.pid"

# Check that server is running after a brief delay
sleep 2
if ps -p $(cat pids/agent_based_llm_ws.pid) > /dev/null; then
    echo "✅ Server is running!"
else
    echo "❌ Server failed to start. Check logs for errors."
fi
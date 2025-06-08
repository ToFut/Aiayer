#!/bin/bash
# Script to start the real DO button executor for physical automation

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Real DO Button Executor - Physical Automation                ║"
echo "║  This will control your mouse and keyboard - Use with caution! ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if the script files exist
if [ ! -f "fixed_agent_do_button_exam.py" ]; then
    echo "Error: fixed_agent_do_button_exam.py not found."
    exit 1
fi

if [ ! -f "real_agent_do_button_executor.py" ]; then
    echo "Error: real_agent_do_button_executor.py not found."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs/executors

# Check if the WebSocket server is already running on port 8767
if lsof -i :8767 &> /dev/null; then
    echo "WebSocket server is already running on port 8767."
    echo "Do you want to use the existing server? (y/n)"
    read -r use_existing
    
    if [[ $use_existing != "y" && $use_existing != "Y" ]]; then
        echo "Killing existing process on port 8767..."
        lsof -ti :8767 | xargs kill -9
        
        # Start a new WebSocket server
        echo "Starting WebSocket server on port 8767..."
        python3 fixed_agent_do_button_exam.py --port 8767 --host localhost --open-browser &
        SERVER_PID=$!
        echo "Server started with PID: $SERVER_PID"
        
        # Give the server time to start
        echo "Waiting for server to start..."
        sleep 3
    fi
else
    # Start a new WebSocket server
    echo "Starting WebSocket server on port 8767..."
    python3 fixed_agent_do_button_exam.py --port 8767 --host localhost --open-browser &
    SERVER_PID=$!
    echo "Server started with PID: $SERVER_PID"
    
    # Give the server time to start
    echo "Waiting for server to start..."
    sleep 3
fi

# Start the real executor
echo "Starting real DO button executor for physical automation..."
echo "IMPORTANT: This will control your mouse and keyboard!"
echo "Press Ctrl+C to stop the executor."
echo ""
echo "⚠️  WARNING: Make sure you have enough screen space cleared for automation."
echo "⚠️  Move your mouse to any screen corner to abort automation (PyAutoGUI failsafe)."
echo ""

# Ask for confirmation
echo "Do you want to continue? (y/n)"
read -r continue

if [[ $continue != "y" && $continue != "Y" ]]; then
    echo "Aborted by user."
    # Kill server if we started it
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID
    fi
    exit 0
fi

# Start the executor
python3 real_agent_do_button_executor.py --host localhost --port 8767 --debug

# Cleanup on exit
if [ -n "$SERVER_PID" ]; then
    echo "Stopping WebSocket server..."
    kill $SERVER_PID
fi

echo "Done."
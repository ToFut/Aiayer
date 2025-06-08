#!/bin/bash

echo "==============================================================="
echo "Real DO Button Physical Automation Test System"
echo "==============================================================="
echo "This test launches the real automation system that performs"
echo "ACTUAL MOUSE AND KEYBOARD ACTIONS on your screen."
echo ""
echo "⚠️  WARNING: Make sure you have enough screen space cleared for automation."
echo "⚠️  Move your mouse to any screen corner to abort automation (PyAutoGUI failsafe)."
echo ""
echo "Press Ctrl+C at any time to stop the test."
echo ""
read -p "Are you sure you want to start the real physical automation test? (y/n): " confirm

if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo "Test cancelled."
    exit 0
fi

# Navigate to project directory
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p logs/websocket
mkdir -p logs/executors
mkdir -p pids

# Stop any existing WebSocket servers on port 8765
if lsof -ti:8765 >/dev/null; then
  echo "Stopping existing WebSocket server on port 8765..."
  lsof -ti:8765 | xargs kill -9 2>/dev/null || true
  sleep 2
fi

# Verify input controller dependencies
echo "Verifying input controller dependencies..."
if ! python3 -c "import pyautogui, pynput" 2>/dev/null; then
    echo "Installing required input controller dependencies..."
    pip3 install pyautogui pynput
fi

# Test input controller
echo "Testing input controller..."
if python3 -c "
import sys
sys.path.append('.')
try:
    from agent_workflow.input_controller import InputController
    controller = InputController()
    print('Input controller initialized successfully')
    controller.stop()
    sys.exit(0)
except Exception as e:
    print(f'Input controller test failed: {str(e)}')
    sys.exit(1)
" 2>/dev/null; then
    echo "✅ Input controller verified"
else
    echo "❌ Input controller test failed"
    echo "Please check that pyautogui and pynput are installed correctly"
    exit 1
fi

# Start the real DO button executor
echo "Starting Real Agent DO Button Executor..."
python3 real_agent_do_button_executor.py --debug > logs/executors/real_agent_do_button_executor.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/real_do_button_executor.pid
echo "Real Agent DO Button Executor PID: $DO_BUTTON_PID"

# Wait for the server to start
sleep 3

# Check if the WebSocket server is running
if lsof -i :8765 > /dev/null 2>&1; then
    echo "✅ Real DO Button Server is listening on port 8765"
else
    echo "❌ Failed to start Real DO Button Server"
    cat logs/executors/real_agent_do_button_executor.log
    exit 1
fi

# Start a simple HTTP server to serve the test HTML
echo "Starting HTTP server for test page..."
python3 -m http.server 8080 --bind 127.0.0.1 > /dev/null 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > pids/http_server.pid

echo ""
echo "==============================================================="
echo "🚀 Real DO Button Test System is running!"
echo "==============================================================="
echo "Open http://localhost:8080/test_real_do_button.html in your browser"
echo "to test the DO button with real physical automation."
echo ""
echo "The page allows you to:"
echo "1. Connect to the WebSocket server"
echo "2. Send test plans (browser search, simple click, text input)"
echo "3. Execute the plans with the DO button"
echo ""
echo "Press Ctrl+C to stop the test system"
echo ""

# Show real-time logs
tail -f logs/executors/real_agent_do_button_executor.log

# Cleanup function
function cleanup {
    echo ""
    echo "Stopping test system..."
    
    # Kill the real DO button executor
    if [ -f "pids/real_do_button_executor.pid" ]; then
        kill -TERM $(cat pids/real_do_button_executor.pid) 2>/dev/null || kill -9 $(cat pids/real_do_button_executor.pid) 2>/dev/null
        rm -f pids/real_do_button_executor.pid
    fi
    
    # Kill the HTTP server
    if [ -f "pids/http_server.pid" ]; then
        kill -TERM $(cat pids/http_server.pid) 2>/dev/null || kill -9 $(cat pids/http_server.pid) 2>/dev/null
        rm -f pids/http_server.pid
    fi
    
    # Clean up any remaining processes
    pkill -f real_agent_do_button_executor 2>/dev/null || true
    
    # Clean up port
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true
    
    echo "Test system stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for user to press Ctrl+C
wait
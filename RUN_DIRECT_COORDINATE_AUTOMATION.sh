#!/bin/bash

echo "==============================================================="
echo "Direct Coordinate Automation System"
echo "==============================================================="
echo "This system provides reliable automation with direct coordinate"
echo "specification, bypassing complex UI detection for more reliable"
echo "mouse/keyboard automation."
echo ""
echo "⚠️  WARNING: Make sure you have enough screen space cleared for automation."
echo "⚠️  Move your mouse to any screen corner to abort automation (PyAutoGUI failsafe)."
echo ""
echo "Press Ctrl+C at any time to stop the test."
echo ""
read -p "Are you sure you want to start the direct coordinate automation system? (y/n): " confirm

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

# Start the direct coordinate automation server
echo "Starting Direct Coordinate Automation Server..."
python3 direct_coordinate_automation.py --debug > logs/websocket/direct_coordinate_automation.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/direct_coordinate_automation.pid
echo "Direct Coordinate Automation Server PID: $DO_BUTTON_PID"

# Wait for the server to start
sleep 3

# Check if the WebSocket server is running
if lsof -i :8765 > /dev/null 2>&1; then
    echo "✅ Direct Coordinate Automation Server is listening on port 8765"
else
    echo "❌ Failed to start Direct Coordinate Automation Server"
    cat logs/websocket/direct_coordinate_automation.log
    exit 1
fi

# Start a simple HTTP server to serve the test HTML
echo "Starting HTTP server for test page..."
python3 -m http.server 8080 --bind 127.0.0.1 > /dev/null 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > pids/http_server.pid

echo ""
echo "==============================================================="
echo "🚀 Direct Coordinate Automation System is running!"
echo "==============================================================="
echo "Open http://localhost:8080/test_direct_coordinate_automation.html in your browser"
echo "to test the DO button with direct coordinate specifications."
echo ""
echo "Features:"
echo "1. Direct Coordinates: Specify exact x,y coordinates for clicking"
echo "2. Real Automation: Performs actual mouse/keyboard actions"
echo "3. Simple Execution: No complex UI detection, just reliable automation"
echo "4. Progress Tracking: Real-time feedback on execution steps"
echo ""
echo "Press Ctrl+C to stop the system"
echo ""

# Show real-time logs
tail -f logs/websocket/direct_coordinate_automation.log

# Cleanup function
function cleanup {
    echo ""
    echo "Stopping test system..."
    
    # Kill the direct automation server
    if [ -f "pids/direct_coordinate_automation.pid" ]; then
        kill -TERM $(cat pids/direct_coordinate_automation.pid) 2>/dev/null || kill -9 $(cat pids/direct_coordinate_automation.pid) 2>/dev/null
        rm -f pids/direct_coordinate_automation.pid
    fi
    
    # Kill the HTTP server
    if [ -f "pids/http_server.pid" ]; then
        kill -TERM $(cat pids/http_server.pid) 2>/dev/null || kill -9 $(cat pids/http_server.pid) 2>/dev/null
        rm -f pids/http_server.pid
    fi
    
    # Clean up any remaining processes
    pkill -f direct_coordinate_automation 2>/dev/null || true
    
    # Clean up port
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true
    
    echo "Test system stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for user to press Ctrl+C
wait
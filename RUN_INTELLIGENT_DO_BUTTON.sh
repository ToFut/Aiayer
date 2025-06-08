#!/bin/bash

echo "==============================================================="
echo "Intelligent DO Button System with Screen Recognition"
echo "==============================================================="
echo "This system provides real mouse/keyboard automation with"
echo "intelligent UI element detection on your screen."
echo ""
echo "⚠️  WARNING: Make sure you have enough screen space cleared for automation."
echo "⚠️  Move your mouse to any screen corner to abort automation (PyAutoGUI failsafe)."
echo ""
echo "Press Ctrl+C at any time to stop the test."
echo ""
read -p "Are you sure you want to start the intelligent automation system? (y/n): " confirm

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

# Start the intelligent DO button server
echo "Starting Intelligent DO Button Server..."
python3 intelligent_do_button_server.py --debug > logs/websocket/intelligent_do_button_server.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/intelligent_do_button_server.pid
echo "Intelligent DO Button Server PID: $DO_BUTTON_PID"

# Wait for the server to start
sleep 3

# Check if the WebSocket server is running
if lsof -i :8765 > /dev/null 2>&1; then
    echo "✅ Intelligent DO Button Server is listening on port 8765"
else
    echo "❌ Failed to start Intelligent DO Button Server"
    cat logs/websocket/intelligent_do_button_server.log
    exit 1
fi

# Start a simple HTTP server to serve the test HTML
echo "Starting HTTP server for test page..."
python3 -m http.server 8080 --bind 127.0.0.1 > /dev/null 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > pids/http_server.pid

echo ""
echo "==============================================================="
echo "🚀 Intelligent DO Button System is running!"
echo "==============================================================="
echo "Open http://localhost:8080/test_intelligent_do_button.html in your browser"
echo "to test the DO button with intelligent UI detection."
echo ""
echo "Features:"
echo "1. Screen Analysis: Detects UI elements automatically"
echo "2. Element Finding: Locates specific elements by name"
echo "3. Automatic Coordinates: Clicks the right spots on screen"
echo "4. Real Automation: Performs actual mouse/keyboard actions"
echo ""
echo "Press Ctrl+C to stop the system"
echo ""

# Show real-time logs
tail -f logs/websocket/intelligent_do_button_server.log

# Cleanup function
function cleanup {
    echo ""
    echo "Stopping test system..."
    
    # Kill the intelligent DO button server
    if [ -f "pids/intelligent_do_button_server.pid" ]; then
        kill -TERM $(cat pids/intelligent_do_button_server.pid) 2>/dev/null || kill -9 $(cat pids/intelligent_do_button_server.pid) 2>/dev/null
        rm -f pids/intelligent_do_button_server.pid
    fi
    
    # Kill the HTTP server
    if [ -f "pids/http_server.pid" ]; then
        kill -TERM $(cat pids/http_server.pid) 2>/dev/null || kill -9 $(cat pids/http_server.pid) 2>/dev/null
        rm -f pids/http_server.pid
    fi
    
    # Clean up any remaining processes
    pkill -f intelligent_do_button_server 2>/dev/null || true
    
    # Clean up port
    lsof -ti:8765 | xargs kill -9 2>/dev/null || true
    
    echo "Test system stopped"
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGINT SIGTERM

# Wait for user to press Ctrl+C
wait
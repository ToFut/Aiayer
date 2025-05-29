#!/bin/bash

# Start TeamViewer UI Automation Test System
# Launches the automation backend and opens the web coordination test interface

echo "🚀 Starting TeamViewer UI Automation Test System..."

# Change to project directory
cd "$(dirname "$0")"

# Check if Python dependencies are available
echo "📦 Checking dependencies..."
python3 -c "import cv2, numpy, pyautogui, websockets, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ Installing required dependencies..."
    pip3 install opencv-python numpy pyautogui websockets pillow
fi

# Kill any existing processes on port 8765
echo "🛑 Stopping any existing services on port 8765..."
lsof -ti:8765 | xargs kill -9 2>/dev/null

# Start the TeamViewer UI Automation System in background
echo "🖥️ Starting TeamViewer UI Automation System..."
python3 teamviewer_ui_automation_system.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started successfully
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Failed to start backend"
    exit 1
fi

# Open the web coordination test in default browser
echo "🌐 Opening web coordination test interface..."
if command -v open >/dev/null 2>&1; then
    # macOS
    open web_coordination_test.html
elif command -v xdg-open >/dev/null 2>&1; then
    # Linux
    xdg-open web_coordination_test.html
else
    echo "📂 Please open web_coordination_test.html in your browser"
fi

echo ""
echo "🎯 TeamViewer UI Automation Test System is running!"
echo ""
echo "🔗 Backend: WebSocket server on ws://localhost:8765"
echo "🌐 Frontend: web_coordination_test.html (should open automatically)"
echo "🖥️ TeamViewer: Integration enabled for remote coordination"
echo ""
echo "✨ Features available:"
echo "   • Real UI element detection"
echo "   • Actual click execution with validation"
echo "   • TeamViewer ID generation and screen sharing"
echo "   • Real-time coordination through WebSocket"
echo "   • Execution plan creation and management"
echo ""
echo "📋 Usage:"
echo "   1. Wait for the web page to connect (green status)"
echo "   2. Enter automation commands like 'click the calculator button'"
echo "   3. Create plans and execute them with DO/ADJUST/DISMISS buttons"
echo "   4. Test clicking on the UI elements in the test panel"
echo "   5. Use TeamViewer features for remote coordination"
echo ""
echo "🛑 To stop: Press Ctrl+C or run: kill $BACKEND_PID"
echo ""

# Keep script running and monitor backend
trap "echo '🛑 Stopping TeamViewer UI Automation System...'; kill $BACKEND_PID 2>/dev/null; exit 0" INT

echo "📊 Monitoring system (Press Ctrl+C to stop)..."
while kill -0 $BACKEND_PID 2>/dev/null; do
    sleep 5
done

echo "❌ Backend process stopped unexpectedly"
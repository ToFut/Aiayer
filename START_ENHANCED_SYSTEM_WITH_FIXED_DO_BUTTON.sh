#!/bin/bash

# SensAI Enhanced Enterprise System Startup with Fixed DO Button
# Includes improved Neural UI integration and guaranteed DO button execution

echo "🚀 Starting Enhanced SensAI Enterprise System with FIXED DO BUTTON..."
echo "🎯 PERFORMANCE-OPTIMIZED + NEURAL UI DETECTOR + FIXED DO BUTTON EXECUTION"
echo "========================================================================"
echo ""

# Create required directories
mkdir -p logs/neural_ui_detector
mkdir -p logs/websocket
mkdir -p logs/do_button
mkdir -p pids

# Helper function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i:$port > /dev/null 2>&1; then
        return 0 # Port is in use
    else
        return 1 # Port is free
    fi
}

# Helper function to kill process by port
kill_process_by_port() {
    local port=$1
    if check_port $port; then
        echo "🛑 Killing process on port $port..."
        lsof -t -i:$port | xargs kill -9 2>/dev/null
        sleep 1
    fi
}

# 1. First kill any existing processes on our required ports
echo "🧹 Cleaning up existing processes..."
kill_process_by_port 8765 # Ultimate DO Button Server
kill_process_by_port 8768 # Neural UI Detector
kill_process_by_port 8766 # Proxy Server
kill_process_by_port 8767 # Backend Server

# 2. Start the Ultimate DO Button Server on port 8765
echo "🚀 Starting Ultimate DO Button Server on port 8765..."

# Check if the WebSocket server script exists
if [ ! -f "ultimate_do_button_server.py" ]; then
    echo "❌ Cannot find ultimate_do_button_server.py"
    echo "Please make sure the file exists in the current directory"
    exit 1
fi

# Start the Ultimate DO Button Server
python3 ultimate_do_button_server.py > logs/do_button/ultimate_do_button_server.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/ultimate_do_button_server.pid
echo "✅ Ultimate DO Button Server started with PID: $DO_BUTTON_PID"

# Give the server a moment to start up
sleep 2

# Check if the server is running
if ! ps -p $DO_BUTTON_PID > /dev/null; then
    echo "❌ ERROR: Ultimate DO Button Server failed to start!"
    echo "Check logs at logs/do_button/ultimate_do_button_server.log"
    exit 1
fi

# 3. Start the Neural UI Detector Server on port 8768
echo "🧠 Starting Neural UI Detector Server on port 8768..."

# Check if the Neural UI Detector script exists
if [ ! -f "neural_ui_detector_server.py" ]; then
    echo "❌ Cannot find neural_ui_detector_server.py"
    echo "Please make sure the file exists in the current directory"
    exit 1
fi

# Copy neural_ui_detector_server.py but modify it to use port 8768 instead of 8765
sed 's/port = 8765/port = 8768/g' neural_ui_detector_server.py > neural_ui_detector_server_8768.py
chmod +x neural_ui_detector_server_8768.py

# Run the modified server
python3 neural_ui_detector_server_8768.py > logs/neural_ui_detector/server.log 2>&1 &
NEURAL_UI_PID=$!
echo $NEURAL_UI_PID > pids/neural_ui_detector_server.pid
echo "✅ Neural UI Detector Server started with PID: $NEURAL_UI_PID"

# Give the server a moment to start up
sleep 2

# Check if the server is running
if ! ps -p $NEURAL_UI_PID > /dev/null; then
    echo "❌ ERROR: Neural UI Detector Server failed to start!"
    echo "Check logs at logs/neural_ui_detector/server.log"
    echo "🧹 Killing DO Button Server and cleaning up..."
    kill -9 $DO_BUTTON_PID 2>/dev/null
    exit 1
fi

# 4. Start the proxy to bridge communication between the two servers
echo "🌉 Starting DO Button Neural UI Proxy..."

# Check if the proxy script exists
if [ ! -f "fix_do_button_connection.py" ]; then
    echo "❌ Cannot find fix_do_button_connection.py"
    echo "Please make sure the file exists in the current directory"
    exit 1
fi

python3 fix_do_button_connection.py > logs/websocket/do_button_neural_proxy.log 2>&1 &
PROXY_PID=$!
echo $PROXY_PID > pids/do_button_neural_proxy.pid
echo "✅ DO Button Neural UI Proxy started with PID: $PROXY_PID"

# Give the proxy a moment to start up
sleep 2

# Check if the proxy is running
if ! ps -p $PROXY_PID > /dev/null; then
    echo "❌ ERROR: DO Button Neural UI Proxy failed to start!"
    echo "Check logs at logs/websocket/do_button_neural_proxy.log"
    echo "🧹 Killing servers and cleaning up..."
    kill -9 $DO_BUTTON_PID 2>/dev/null
    kill -9 $NEURAL_UI_PID 2>/dev/null
    exit 1
fi

# 5. Start the Enhanced System
echo "🏢 Starting the Enhanced Enterprise Backend..."

# Source the original script but capture its output instead of displaying it
source <(cat START_ENHANCED_SYSTEM.sh | sed '/^Press Ctrl+C to stop showing logs/,$ d')

# Create a custom stop script
cat > STOP_ENHANCED_SYSTEM_WITH_FIXED_DO_BUTTON.sh << 'EOL'
#!/bin/bash

echo "🛑 Stopping Enhanced System with Fixed DO Button..."

# Kill all processes from PIDs
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            echo "🛑 Stopping $COMPONENT (PID: $PID)"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Kill any remaining processes on specific ports
kill_port() {
    if lsof -i:$1 > /dev/null 2>&1; then
        echo "🛑 Killing process on port $1..."
        lsof -t -i:$1 | xargs kill -9 2>/dev/null
    fi
}

kill_port 8765  # Ultimate DO Button Server
kill_port 8768  # Neural UI Detector
kill_port 8766  # Proxy Server
kill_port 8767  # Backend Server

echo "✅ All components have been stopped."
EOL

chmod +x STOP_ENHANCED_SYSTEM_WITH_FIXED_DO_BUTTON.sh

echo ""
echo "🎉 COMPLETE ENHANCED SYSTEM WITH FIXED DO BUTTON READY!"
echo "================================================================="
echo "🏢 Enhanced Enterprise Backend: ws://localhost:8767"
echo "🔧 Ultimate DO Button Server: ws://localhost:8765"
echo "🧠 Neural UI Detector Server: ws://localhost:8768"
echo "🌉 DO Button Neural UI Proxy: ws://localhost:8766"
echo ""
echo "📱 How to Test DO Button Fix:"
echo "   1. Open the overlay chat interface"
echo "   2. Use Agent mode to create a plan"
echo "   3. Click the DO button - it should now execute properly!"
echo ""
echo "📊 Live System Status:"
echo "   DO Button Server PID: $DO_BUTTON_PID"
echo "   Neural UI Detector PID: $NEURAL_UI_PID"
echo "   DO Button Neural UI Proxy PID: $PROXY_PID"
echo "   Enhanced Backend PID: $BACKEND_PID"
echo "   Process Sensor PID: $PROCESS_PID"
echo "   Screen Sensor PID: $SCREEN_PID"
echo ""
echo "📊 Live Logs:"
echo "   DO Button Server: tail -f logs/do_button/ultimate_do_button_server.log"
echo "   Neural UI Detector: tail -f logs/neural_ui_detector/server.log"
echo "   DO Button Neural UI Proxy: tail -f logs/websocket/do_button_neural_proxy.log"
echo "   Backend: tail -f logs/backend/enhanced_enterprise_8767.log"
echo ""
echo "🛑 Stop System: ./STOP_ENHANCED_SYSTEM_WITH_FIXED_DO_BUTTON.sh"
echo ""
echo "Press Ctrl+C to stop showing logs (system will keep running)"
echo "----------------------------------------"

# Show live logs from the DO Button server
tail -f logs/do_button/ultimate_do_button_server.log logs/websocket/do_button_neural_proxy.log 2>/dev/null | sed 's/^/[DO-BUTTON-SYSTEM] /' || {
    echo "📊 System running in background..."
}
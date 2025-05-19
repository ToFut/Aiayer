#!/bin/bash

# Enable error reporting and debugging
set -e
set -x

echo "==== Checking Environment ===="

# Check if we're already in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Already in virtual environment: $VIRTUAL_ENV"
else
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        echo "Found virtual environment, activating..."
        source venv/bin/activate || {
            echo "Failed to activate virtual environment"
            exit 1
        }
    else
        echo "Warning: No virtual environment found"
    fi
fi

# Verify Python environment
echo "Verifying Python environment..."
which python || {
    echo "Python not found in PATH"
    exit 1
}

python --version || {
    echo "Failed to get Python version"
    exit 1
}

# Check required files
echo "Checking required files..."
if [ ! -f "overlay/desktop_widget.html" ]; then
    echo "Error: Widget HTML file not found at overlay/desktop_widget.html"
    exit 1
fi

if [ ! -f "connect_all_components.py" ]; then
    echo "Error: connect_all_components.py not found"
    exit 1
fi

if [ ! -f "run_widget.py" ]; then
    echo "Error: run_widget.py not found"
    exit 1
fi

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Kill existing processes
echo "Cleaning up existing processes..."
pkill -f "python.*overlay_ws_server" || true
pkill -f "python.*bridge" || true
pkill -f "python.*server.py" || true
pkill -f "python.*connect_all_components.py" || true

echo "==== Starting All Components ===="

# Start the connector in the background
echo "Starting connector..."
python connect_all_components.py > logs/all_components.log 2>&1 &
CONNECTOR_PID=$!

# Verify the connector started
if ! ps -p $CONNECTOR_PID > /dev/null; then
    echo "Error: Failed to start connector"
    echo "=== Connector Log ==="
    cat logs/all_components.log
    exit 1
fi

# Wait for WebSocket server to start
echo "Waiting for WebSocket server to start..."
for i in {1..30}; do
    python -c "import socket; s=socket.socket(); s.settimeout(1); exit(0) if s.connect_ex(('127.0.0.1', 8767)) == 0 else exit(1)" && break
    if [ $i -eq 30 ]; then
        echo "Error: WebSocket server failed to start"
        echo "=== Connector Log ==="
        cat logs/all_components.log
        exit 1
    fi
    echo "Waiting for WebSocket server... ($i/30)"
    sleep 1
done

# Start the widget
echo "Starting widget..."
python run_widget.py 2>&1 | tee logs/widget.log

# Clean up when widget exits
echo "Cleaning up..."
kill $CONNECTOR_PID || true
echo "All components stopped"
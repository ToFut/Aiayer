#!/bin/bash
# Force stop script for Local Assistant
# Forcefully terminates all components of the system to ensure a clean restart

echo "========================================"
echo "Local Assistant Force Stop Tool"
echo "========================================"
echo "This script will forcefully terminate all Local Assistant components."
echo "Use this when the system is unresponsive or before a clean restart."
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Log the force stop
echo "[$(date)] Running force_stop.sh" >> logs/system_fixes.log

# Function to check if a process is running
is_running() {
  pgrep -f "$1" > /dev/null
  return $?
}

# Count processes before stopping
PYTHON_COUNT=$(pgrep -f "python.*local_assistant" | wc -l)
WEBSOCKET_COUNT=$(pgrep -f "websocket_server.py" | wc -l)
OVERLAY_COUNT=$(pgrep -f "main_with_overlay.py" | wc -l)

echo "Found processes before stopping:"
echo "Python processes: $PYTHON_COUNT"
echo "WebSocket processes: $WEBSOCKET_COUNT"
echo "Overlay processes: $OVERLAY_COUNT"
echo ""

# First, try graceful termination
echo "Attempting graceful termination..."
if is_running "main_with_overlay.py"; then
  echo "Stopping main application..."
  pkill -f "main_with_overlay.py"
fi

if is_running "websocket_server.py"; then
  echo "Stopping WebSocket server..."
  pkill -f "websocket_server.py"
fi

# Wait a moment for processes to terminate
echo "Waiting for processes to terminate..."
sleep 3

# Force kill any remaining processes
REMAINING=$(pgrep -f "python.*local_assistant" | wc -l)
if [ $REMAINING -gt 0 ]; then
  echo "$REMAINING processes still running. Force terminating..."
  pkill -9 -f "python.*local_assistant"
  sleep 1
fi

# Check ports and release if needed
echo ""
echo "Checking for occupied ports..."

# Function to check if a port is in use
is_port_used() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i :$1 >/dev/null 2>&1
    return $?
  elif command -v netstat >/dev/null 2>&1; then
    netstat -tuln | grep ":$1 " >/dev/null 2>&1
    return $?
  else
    # Fallback to a simple socket check
    (echo > /dev/tcp/127.0.0.1/$1) >/dev/null 2>&1
    return $?
  fi
}

# Check and release common ports used by the system
for PORT in 8765 5002 8080 6789; do
  if is_port_used $PORT; then
    echo "Port $PORT is still in use. Attempting to release it..."
    
    # Find process using the port
    if command -v lsof >/dev/null 2>&1; then
      PID=$(lsof -t -i:$PORT 2>/dev/null)
    elif command -v netstat >/dev/null 2>&1 && command -v grep >/dev/null 2>&1 && command -v awk >/dev/null 2>&1; then
      PID=$(netstat -tlnp 2>/dev/null | grep ":$PORT " | awk '{print $7}' | cut -d'/' -f1)
    fi
    
    if [ -n "$PID" ]; then
      echo "Terminating process $PID using port $PORT..."
      kill -9 $PID 2>/dev/null
    else
      echo "Could not identify process using port $PORT."
    fi
  else
    echo "Port $PORT is free."
  fi
done

# Clean up temporary files
echo ""
echo "Cleaning up temporary files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +>/dev/null 2>&1 || true

# Touch log files to ensure they exist with proper permissions
echo "Resetting log files..."
mkdir -p logs
touch logs/main.log logs/websocket.log logs/llm_model.log logs/overlay.log

# Final verification
REMAINING=$(pgrep -f "python.*local_assistant" | wc -l)
if [ $REMAINING -gt 0 ]; then
  echo ""
  echo "Warning: $REMAINING processes could not be terminated."
  echo "You may need to manually terminate these processes:"
  pgrep -af "python.*local_assistant"
else
  echo ""
  echo "All Local Assistant processes have been terminated successfully."
fi

# Check if Ollama is running and responsive
echo ""
echo "Checking Ollama status..."
if is_running "ollama"; then
  echo "Ollama is running."
  if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "Ollama is responding correctly."
  else
    echo "Warning: Ollama is running but not responding."
    echo "You may want to restart Ollama with:"
    echo "pkill -f ollama && ollama serve"
  fi
else
  echo "Ollama is not running."
fi

echo ""
echo "========================================"
echo "Force stop completed"
echo "You can now restart the system with fix_system.sh"
echo "========================================"

# Log completion
echo "[$(date)] force_stop.sh completed" >> logs/system_fixes.log
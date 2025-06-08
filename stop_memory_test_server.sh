#!/bin/bash

echo "Stopping Memory Test Servers..."

# Directory for PIDs
PID_DIR="pids"
mkdir -p "$PID_DIR"

# Stop WebSocket server
if [ -f "${PID_DIR}/memory_test_ws_server.pid" ]; then
  WS_PID=$(cat "${PID_DIR}/memory_test_ws_server.pid")
  if ps -p $WS_PID > /dev/null; then
    echo "Stopping WebSocket server (PID: $WS_PID)..."
    kill $WS_PID
    echo "WebSocket server stopped."
  else
    echo "WebSocket server not running (PID: $WS_PID)."
  fi
  rm -f "${PID_DIR}/memory_test_ws_server.pid"
else
  echo "No WebSocket server PID file found, looking for Python process..."
  # Find by process name if PID file not found
  WS_PIDS=$(ps aux | grep "memory_test_server.py" | grep -v grep | awk '{print $2}')
  if [ ! -z "$WS_PIDS" ]; then
    echo "Found WebSocket server processes..."
    for pid in $WS_PIDS; do
      echo "Stopping process with PID: $pid..."
      kill -9 $pid
    done
    echo "WebSocket server stopped."
  fi
fi

# Stop HTTP server
if [ -f "${PID_DIR}/memory_test_http_server.pid" ]; then
  HTTP_PID=$(cat "${PID_DIR}/memory_test_http_server.pid")
  if ps -p $HTTP_PID > /dev/null; then
    echo "Stopping HTTP server (PID: $HTTP_PID)..."
    kill $HTTP_PID
    echo "HTTP server stopped."
  else
    echo "HTTP server not running (PID: $HTTP_PID)."
  fi
  rm -f "${PID_DIR}/memory_test_http_server.pid"
else
  echo "No HTTP server PID file found, looking for Python HTTP server process..."
  # Find by process name if PID file not found
  HTTP_PID=$(ps aux | grep "http.server" | grep "8081" | grep -v grep | awk '{print $2}')
  if [ ! -z "$HTTP_PID" ]; then
    echo "Found HTTP server process (PID: $HTTP_PID)..."
    kill $HTTP_PID
    echo "HTTP server stopped."
  fi
fi

echo "Memory Test Servers shutdown complete."
#!/bin/bash
# Script to kill any running HTTP servers

echo "=== Stopping HTTP servers ==="

# Kill Python's http.server on port 8080
pid=$(lsof -ti :8080 2>/dev/null)
if [ -n "$pid" ]; then
  echo "Found HTTP server on port 8080 (PID: $pid), killing..."
  kill -9 $pid 2>/dev/null && echo "Killed process $pid" || echo "Failed to kill process $pid"
else
  echo "No HTTP server found on port 8080"
fi

# Kill simple_http_server
pid=$(ps aux | grep "simple_http_server" | grep -v grep | awk '{print $2}')
if [ -n "$pid" ]; then
  echo "Found simple_http_server (PID: $pid), killing..."
  kill -9 $pid 2>/dev/null && echo "Killed process $pid" || echo "Failed to kill process $pid"
else
  echo "No simple_http_server found"
fi

# Remove HTTP server PID file
if [ -f "pids/http_server.pid" ]; then
  echo "Removing pids/http_server.pid"
  rm -f pids/http_server.pid
else
  echo "No pids/http_server.pid file found"
fi

echo "HTTP server cleanup complete"
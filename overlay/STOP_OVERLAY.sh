#!/bin/bash

# Script to stop all overlay components
echo "Stopping overlay system..."

# Kill overlay processes
echo "Stopping overlay application..."
pkill -f ai-assistant-overlay 2>/dev/null || true
pkill -f vite 2>/dev/null || true
pkill -f tauri 2>/dev/null || true

# Kill WebSocket servers
echo "Stopping WebSocket servers..."
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true
lsof -ti:8768 | xargs kill -9 2>/dev/null || true

# Kill other related processes
echo "Stopping other related processes..."
pkill -f fixed_bridge_server 2>/dev/null || true
pkill -f minimal_ws_server 2>/dev/null || true
pkill -f enhanced_enterprise_backend 2>/dev/null || true

# Remove pid files
echo "Cleaning up PID files..."
rm -f pids/*.pid 2>/dev/null || true

echo "✅ Overlay system stopped!"
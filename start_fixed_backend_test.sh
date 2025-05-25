#!/bin/bash

echo "🚀 Starting Fixed Backend with Visual Memory Integration Test"

# Create logs directory if it doesn't exist
mkdir -p logs/backend

# Start the fixed backend in the background
echo "Starting fixed backend on port 8767..."
python3 enterprise_backend_8767_with_fixed_visual_memory.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 3

# Test the integration
echo "Testing fixed visual memory integration..."
python3 test_fixed_backend_visual_integration.py

# Kill the backend
echo "Stopping backend..."
kill $BACKEND_PID 2>/dev/null

echo "✅ Test completed!"
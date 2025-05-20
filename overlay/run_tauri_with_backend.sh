#!/bin/bash
# Script to run Tauri with the existing backend services

# First, start the backend system in a separate terminal/process
cd ..
echo "Starting the optimized system with LLM..."
./start_optimized_system_with_llm.sh &
BACKEND_PID=$!

# Give the backend system time to start
echo "Waiting for backend services to initialize..."
sleep 5

# Now start the Tauri application
cd overlay
echo "Starting Tauri application..."
npm run tauri dev

# When the Tauri app exits, clean up the backend processes
echo "Cleaning up backend processes..."
# Use the existing shutdown function from the backend script
kill -TERM $BACKEND_PID

echo "All processes have been stopped."
#!/bin/bash
# Script to rebuild the overlay application with updated configuration and run the integrated memory system

echo "Starting rebuild and run process..."

# Step 1: First start the backend services
echo "Starting background services..."
bash ./improved_run_integrated_memory_system.sh &
BACKEND_PID=$!

# Sleep to allow backend services to initialize
echo "Waiting for backend services to initialize..."
sleep 5

# Step 2: Change directory to overlay
cd "$(dirname "$0")/overlay"

# Step 3: Start Tauri dev mode
echo "Starting Tauri overlay in development mode..."
npm run tauri dev

# When Tauri exits, kill the background processes
kill $BACKEND_PID
echo "Shut down background services."
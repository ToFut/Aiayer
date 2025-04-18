#!/bin/bash

# Kill all related processes
echo "Killing existing processes..."
pkill -f "python.*main.py"
pkill -f "npm.*tauri dev"
pkill -f "vite"
pkill -f "ollama"

# Kill processes on specific ports
for port in 5001 1420 1421 11434 8765; do
    lsof -ti :$port | xargs kill -9 2>/dev/null
done

# Wait for processes to terminate
sleep 2

# Start Ollama in the background
echo "Starting Ollama..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
sleep 5

# Start the main Python application in the background
echo "Starting main application..."
python main.py &
MAIN_PID=$!

# Wait for the main application to start
sleep 5

# Start the overlay application
echo "Starting overlay application..."
cd overlay
npm run tauri dev &
OVERLAY_PID=$!

# Store PIDs in .running_pids file
echo "$OLLAMA_PID $MAIN_PID $OVERLAY_PID" > ../.running_pids

# Wait for all processes
wait
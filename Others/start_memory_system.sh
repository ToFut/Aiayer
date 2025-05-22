#!/bin/bash
# Script to start the conscious memory system

# Set working directory to the script location
cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Default update interval (can be overridden with -i flag)
UPDATE_INTERVAL=30
VERBOSE=false

# Parse command line arguments
while getopts "i:v" opt; do
  case $opt in
    i) UPDATE_INTERVAL=$OPTARG ;;
    v) VERBOSE=true ;;
    *) echo "Usage: $0 [-i interval_seconds] [-v]"; exit 1 ;;
  esac
done

echo "Starting Conscious Memory System"
echo "================================"
echo "Update interval: ${UPDATE_INTERVAL} seconds"
echo "Verbose mode: ${VERBOSE}"
echo "Logs will be saved to logs/memory_runner.log"
echo "Press Ctrl+C to stop"
echo "================================"

# Start the memory update runner
if [ "$VERBOSE" = true ]; then
    python3 run_memory_update.py --interval $UPDATE_INTERVAL --verbose
else
    python3 run_memory_update.py --interval $UPDATE_INTERVAL
fi
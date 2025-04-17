#!/bin/bash

# Run script for Local AI Assistant with Overlay

# Create necessary directories
mkdir -p logs
mkdir -p config

# Set up Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install Flask python-dotenv flask-cors pyyaml pillow flask-sock mss pytesseract watchdog websockets requests

# Get directory of script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a modified version of main.py that includes the overlay bridge
cat > "$DIR/start_overlay.py" << 'EOF'
#!/usr/bin/env python3
"""
Script to start the overlay bridge and WebSocket server
"""
import logging
import asyncio
import signal
import sys
import os
from agent.overlay_bridge import OverlayBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize the overlay bridge
overlay_bridge = OverlayBridge(port=8765)
bridge_thread = None

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal...")
    if bridge_thread:
        overlay_bridge.stop()
    sys.exit(0)

def main():
    """Start the overlay bridge"""
    logger.info("Starting overlay bridge on port 8765...")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the overlay bridge in a background thread
    bridge_thread = overlay_bridge.start()
    logger.info("Overlay bridge started")
    
    # Keep the main thread running
    try:
        # Keep the script running
        while True:
            try:
                line = input("Overlay server running. Type 'exit' to stop: ")
                if line.lower() == 'exit':
                    break
            except KeyboardInterrupt:
                break
            except EOFError:
                # Handle EOF (when running in background)
                break
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down...")
        if bridge_thread:
            overlay_bridge.stop()
        
if __name__ == "__main__":
    main()
EOF

# Make the new script executable
chmod +x "$DIR/start_overlay.py"

# Set environment variables
export PYTHONPATH=.

echo "Starting the overlay bridge..."
python3 "$DIR/start_overlay.py" &
BRIDGE_PID=$!

# Sleep for a moment to let the server start
sleep 2

# Instructions for starting the Tauri overlay
echo "========================================================"
echo "WebSocket bridge is running on port 8765"
echo ""
echo "To start the overlay application, open a new terminal and run:"
echo ""
echo "cd $DIR/overlay"
echo "npm run tauri dev"
echo ""
echo "Press Ctrl+C to stop the bridge"
echo "========================================================"

# Wait for the bridge to exit
wait $BRIDGE_PID
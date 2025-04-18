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

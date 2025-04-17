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

async def shutdown(signal, loop):
    """Shutdown the application gracefully"""
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

def main():
    """Start the overlay bridge"""
    logger.info("Starting overlay bridge on port 8765...")
    
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
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down...")
        # Note: The bridge is running in a daemon thread, so it will terminate when the main thread exits
        
if __name__ == "__main__":
    main()

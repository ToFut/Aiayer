#!/usr/bin/env python3
"""
Bridge Server Starter
Starts the WebSocket bridge server for communication between frontend and backend.
"""
import asyncio
import logging
import os
from bridge.server import BridgeServer

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    # Create and start the bridge server
    server = BridgeServer(host="localhost", frontend_port=8765, backend_port=8766)
    
    try:
        # Save PID
        os.makedirs('pids', exist_ok=True)
        with open('pids/bridge_server.pid', 'w') as f:
            f.write(str(os.getpid()))
            
        logger.info("Starting bridge server...")
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        exit(1) 
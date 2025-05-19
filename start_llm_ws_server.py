#!/usr/bin/env python3
"""
Start LLM WebSocket Server for Integration with start_optimized_system_fixed.sh
"""
import os
import sys
import logging
from llm_ws_module import run_as_module

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/start_llm_ws_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the script."""
    logger.info("Starting LLM WebSocket Server")
    
    try:
        # Ensure pids directory exists
        os.makedirs("pids", exist_ok=True)
        
        # Start the server through the module
        run_as_module()
        
        # Note: This point will only be reached if the server exits
        return 0
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
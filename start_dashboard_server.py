#!/usr/bin/env python3
"""
Start Dashboard Server

Script to start the task memory dashboard web server
"""

import os
import sys
import logging
import asyncio
import time
from importlib import import_module
import uvicorn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dashboard_launcher")

# Ensure required directories exist
os.makedirs('logs/dashboard', exist_ok=True)
os.makedirs('web/dashboard/static/css', exist_ok=True)
os.makedirs('web/dashboard/static/js', exist_ok=True)
os.makedirs('web/dashboard/templates', exist_ok=True)

async def start_dashboard():
    try:
        # Import the dashboard server module
        logger.info("Importing dashboard server module")
        from memory.dashboard_server import app
        
        # Log successful import
        logger.info("Dashboard server module imported successfully")
        
        # Start the server using uvicorn
        logger.info("Starting FastAPI dashboard server on port 8081")
        config = uvicorn.Config(app, host="0.0.0.0", port=8081, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
        
    except ImportError as e:
        logger.error(f"Failed to import dashboard server: {e}")
        print(f"Error: Failed to import dashboard server: {e}")
        return None
    except Exception as e:
        logger.error(f"Error starting dashboard server: {e}")
        print(f"Error: Failed to start dashboard server: {e}")
        return None

def main():
    try:
        # Print startup message
        print("\n======= Task Memory Dashboard =======")
        print("Starting dashboard server on http://localhost:8081")
        
        # Run the asyncio event loop
        asyncio.run(start_dashboard())
            
    except KeyboardInterrupt:
        print("\nDashboard server startup cancelled")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
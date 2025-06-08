#!/usr/bin/env python3
"""
Memory Dashboard Connector
Initializes and connects the memory system and dashboard.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import websockets
from typing import Dict, Any, Optional

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_connector')

class MemoryConnector:
    """Connector for memory system and dashboard."""
    
    def __init__(self, memory_system_uri="ws://localhost:8765", dashboard_uri="ws://localhost:8082"):
        """Initialize the memory connector."""
        self.memory_system_uri = memory_system_uri
        self.dashboard_uri = dashboard_uri
        self.running = True
        self.memory_system = None
        self.dashboard = None
        
        logger.info("Memory connector initialized")
    
    async def start(self):
        """Start the memory connector."""
        try:
            # Connect to memory system
            await self._connect_to_memory_system()
            
            # Connect to dashboard
            await self._connect_to_dashboard()
            
            # Keep connector running
            while self.running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error starting memory connector: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def _connect_to_memory_system(self):
        """Connect to the memory system."""
        while self.running:
            try:
                async with websockets.connect(self.memory_system_uri) as websocket:
                    self.memory_system = websocket
                    logger.info("Connected to memory system")
                    
                    while self.running:
                        try:
                            # Receive memory state updates
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Forward to dashboard if connected
                            if self.dashboard:
                                await self.dashboard.send(message)
                            
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Connection to memory system closed")
                            break
                        except Exception as e:
                            logger.error(f"Error in memory system communication: {e}")
                            logger.error(traceback.format_exc())
                            break
                    
            except Exception as e:
                logger.error(f"Error connecting to memory system: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    
    async def _connect_to_dashboard(self):
        """Connect to the memory dashboard."""
        while self.running:
            try:
                async with websockets.connect(self.dashboard_uri) as websocket:
                    self.dashboard = websocket
                    logger.info("Connected to memory dashboard")
                    
                    while self.running:
                        try:
                            # Receive dashboard requests
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Forward to memory system if connected
                            if self.memory_system:
                                await self.memory_system.send(message)
                            
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Connection to memory dashboard closed")
                            break
                        except Exception as e:
                            logger.error(f"Error in dashboard communication: {e}")
                            logger.error(traceback.format_exc())
                            break
                    
            except Exception as e:
                logger.error(f"Error connecting to memory dashboard: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop the memory connector."""
        self.running = False
        if self.memory_system:
            await self.memory_system.close()
        if self.dashboard:
            await self.dashboard.close()
        logger.info("Memory connector stopped")

async def main():
    """Main function to run the memory connector."""
    try:
        # Create and start connector
        connector = MemoryConnector()
        await connector.start()
        
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Error in memory connector: {e}")
        logger.error(traceback.format_exc())
    finally:
        if 'connector' in locals():
            await connector.stop()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 
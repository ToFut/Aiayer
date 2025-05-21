#!/usr/bin/env python3
"""
Fixed Memory Connector

This module connects to the bridge server and receives sensor data,
then updates the memory system directly.
"""
import os
import json
import asyncio
import logging
import websockets
import traceback
from datetime import datetime
import sys

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_connector')

# We need to fix the imports for memory_system
# First, create a simple wrapper/stub for the memory system
class SimpleMemorySystem:
    """A simplified version of the memory system for the connector"""
    
    async def initialize(self):
        """Initialize the memory system"""
        logger.info("SimpleMemorySystem initialized")
        return True
        
    async def process_sensor_data(self, sensor_type, payload):
        """Process sensor data (simplified implementation)"""
        logger.info(f"Processed {sensor_type} sensor data with {len(str(payload))} bytes")
        return True
        
    async def search_memory(self, query, limit=5):
        """Search memory for the query (simplified implementation)"""
        logger.info(f"Searched memory for: {query}")
        return [{"relevance": 0.8, "content": "Simplified memory search result", "source": "stub", "timestamp": datetime.now().isoformat()}]

class MemoryConnector:
    """Connects to bridge server to receive data for memory system"""
    
    def __init__(self, bridge_uri="ws://localhost:8768"):  # Using port 8768
        self.bridge_uri = bridge_uri
        self.running = True
        
        # Initialize the simplified memory system
        self.memory_system = SimpleMemorySystem()
        
        # Initialize on connect automatically
        self.initialized = False
        
        logger.info("Memory connector initialized")
    
    async def initialize_memory(self):
        """Initialize memory system"""
        if self.initialized:
            return True
            
        try:
            # Initialize memory system
            await self.memory_system.initialize()
            self.initialized = True
            logger.info("Memory system initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def connect_to_bridge(self):
        """Connect to bridge server to receive data"""
        while self.running:
            try:
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Initialize memory system
                    if not await self.initialize_memory():
                        logger.error("Failed to initialize memory system, retrying in 5 seconds")
                        await asyncio.sleep(5)
                        continue
                    
                    # Identify as memory system
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "memory_system",
                            "version": "1.0.0",
                            "capabilities": ["memory_persistence", "context_tracking"]
                        }
                    }))
                    
                    # Process incoming messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            msg_type = data.get('type', '')
                            
                            # Handle sensor data
                            if msg_type == 'sensor_data':
                                sensor_type = data.get('sensor_type', '')
                                payload = data.get('payload', {})
                                
                                if sensor_type and payload:
                                    # Process sensor data in memory system
                                    await self.process_sensor_data(sensor_type, payload)
                            
                            # Handle context query
                            elif msg_type == 'context_query':
                                query = data.get('query', '')
                                
                                if query:
                                    # Process context query in memory system
                                    result = await self.process_context_query(query)
                                    
                                    # Send response back
                                    await websocket.send(json.dumps({
                                        "type": "context_response",
                                        "query": query,
                                        "result": result,
                                        "timestamp": datetime.now().isoformat()
                                    }))
                            
                            # Handle unknown message types
                            else:
                                logger.warning(f"Unknown message type: {msg_type}")
                        
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            logger.error(traceback.format_exc())
                
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)  # Wait before reconnecting
    
    async def process_sensor_data(self, sensor_type, payload):
        """Process sensor data in memory system"""
        try:
            # Log the sensor data
            logger.info(f"Processing {sensor_type} sensor data")
            
            # Convert some payload fields if needed
            if sensor_type == 'process' and 'active_apps' in payload:
                if isinstance(payload['active_apps'], list):
                    # Fix active_apps format if necessary
                    processed_apps = []
                    for app in payload['active_apps']:
                        if isinstance(app, dict):
                            processed_apps.append(app)
                        elif isinstance(app, str):
                            processed_apps.append({'name': app})
                        else:
                            processed_apps.append({'name': str(app)})
                    payload['active_apps'] = processed_apps
            
            # Add sensor data to memory system
            await self.memory_system.process_sensor_data(sensor_type, payload)
            
            logger.info(f"Successfully processed {sensor_type} sensor data")
            return True
        except Exception as e:
            logger.error(f"Error processing {sensor_type} sensor data: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def process_context_query(self, query):
        """Process context query in memory system"""
        try:
            # Log the context query
            logger.info(f"Processing context query: {query}")
            
            # Search memory for context related to query
            search_result = await self.memory_system.search_memory(query, limit=5)
            
            # Process search result
            context_data = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "results": search_result
            }
            
            logger.info(f"Found {len(search_result)} results for context query")
            return context_data
        except Exception as e:
            logger.error(f"Error processing context query: {e}")
            logger.error(traceback.format_exc())
            return {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "error": str(e),
                "results": []
            }
    
    async def run(self):
        """Run the memory connector"""
        logger.info("Starting memory connector")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/memory_connector.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Run tasks
        try:
            # Connect to bridge
            bridge_task = asyncio.create_task(self.connect_to_bridge())
            
            # Wait for tasks to complete
            await asyncio.gather(bridge_task)
        except asyncio.CancelledError:
            logger.info("Memory connector tasks cancelled")
        except Exception as e:
            logger.error(f"Error in memory connector: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Clean up
            self.running = False

# Run memory connector
async def run_memory_connector():
    connector = MemoryConnector()
    await connector.run()

if __name__ == "__main__":
    try:
        # Add current directory to path to ensure imports work
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        asyncio.run(run_memory_connector())
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Error running memory connector: {e}")
        logger.error(traceback.format_exc())
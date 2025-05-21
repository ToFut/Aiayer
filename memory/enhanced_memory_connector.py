#!/usr/bin/env python3
"""
Enhanced Memory Connector

This module connects to the bridge server and receives sensor data,
then updates the memory system.
"""
import os
import json
import asyncio
import logging
import websockets
import traceback
import time
from datetime import datetime

# Import enhanced memory classes
import sys
# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Direct import from the current directory
from memory_system import MemorySystem

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

class MemoryConnector:
    """Connects to bridge server to receive data for memory system"""
    
    def __init__(self, bridge_uri="ws://localhost:8768"):  # Changed from 8767 to 8768
        self.bridge_uri = bridge_uri
        self.running = True
        
        # Initialize memory system
        self.memory_system = MemorySystem()
        
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
        # Keep track of registration state
        registered = False
        connection_attempts = 0
        
        while self.running:
            try:
                # Initialize memory system first
                if not await self.initialize_memory():
                    logger.error("Failed to initialize memory system, retrying in 5 seconds")
                    await asyncio.sleep(5)
                    continue
                
                # Connect to bridge server
                async with websockets.connect(self.bridge_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.bridge_uri}")
                    
                    # Reset attempt counter on successful connection
                    connection_attempts = 0
                    registered = False
                    
                    # Register with bridge server - always send registration on new connection
                    await websocket.send(json.dumps({
                        "type": "register",
                        "client_type": "memory",
                        "version": "1.0.0",
                        "capabilities": ["memory_persistence", "context_tracking"]
                    }))
                    
                    # Wait for registration confirmation before proceeding
                    registration_timeout = 5  # seconds to wait for confirmation
                    try:
                        registration_start = time.time()
                        while not registered and time.time() - registration_start < registration_timeout:
                            try:
                                # Use a timeout for receiving the registration confirmation
                                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                                data = json.loads(response)
                                msg_type = data.get('type', '')
                                
                                if msg_type == 'registration_confirmed':
                                    registered = True
                                    logger.info("Registration confirmed with bridge server")
                                    break
                                elif msg_type == 'error':
                                    error_msg = data.get('message', 'Unknown error')
                                    logger.warning(f"Registration error: {error_msg}")
                                    if "Registration required" in error_msg:
                                        # Try registering again
                                        logger.info("Received registration required message, sending registration again")
                                        await websocket.send(json.dumps({
                                            "type": "register",
                                            "client_type": "memory",
                                            "version": "1.0.0",
                                            "capabilities": ["memory_persistence", "context_tracking"]
                                        }))
                                        # Wait a moment to allow the server to process the registration
                                        await asyncio.sleep(0.5)
                            except asyncio.TimeoutError:
                                # Timeout waiting for response, try again
                                continue
                            except Exception as e:
                                logger.error(f"Error waiting for registration confirmation: {e}")
                                break
                                
                        # Check if registration failed
                        if not registered:
                            logger.warning("Failed to receive registration confirmation, closing connection")
                            continue
                        else:
                            # Add a brief pause after successful registration before sending any other messages
                            logger.info("Registration successful, pausing briefly before proceeding with message loop")
                            await asyncio.sleep(1)
                            
                            # Start heartbeat task to keep connection alive
                            heartbeat_task = asyncio.create_task(self.heartbeat(websocket))
                            
                            # Send a keep-alive ping to maintain the connection
                            try:
                                await websocket.send(json.dumps({
                                    "type": "ping",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                logger.info("Sent keep-alive ping after registration")
                            except Exception as e:
                                logger.error(f"Error sending keep-alive ping: {e}")
                                heartbeat_task.cancel()
                                continue
                    except Exception as e:
                        logger.error(f"Error during registration process: {e}")
                        continue
                    
                    # Process incoming messages after successful registration
                    try:
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                msg_type = data.get('type', '')
                                
                                # Check for registration confirmation
                                if msg_type == 'registration_confirmed':
                                    registered = True
                                    logger.info("Registration confirmed with bridge server")
                                
                                # Handle ping response (pong)
                                elif msg_type == 'pong':
                                    logger.debug("Received pong from server")
                                
                                # Handle sensor data
                                elif msg_type == 'sensor_data':
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
                    finally:
                        # Make sure to cancel the heartbeat task when the connection is closed
                        if 'heartbeat_task' in locals() and heartbeat_task is not None:
                            logger.info("Cancelling heartbeat task")
                            heartbeat_task.cancel()
                            try:
                                await heartbeat_task
                            except asyncio.CancelledError:
                                pass
                
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                connection_attempts += 1
                backoff = min(5 * connection_attempts, 60)  # Exponential backoff capped at 60 seconds
                logger.warning(f"Connection to bridge server failed: {e}, retrying in {backoff} seconds (attempt {connection_attempts})")
                # Reset registration state on connection failure
                registered = False  
                await asyncio.sleep(backoff)
            except Exception as e:
                connection_attempts += 1 
                backoff = min(5 * connection_attempts, 60)
                logger.error(f"Unexpected error: {e}, retrying in {backoff} seconds (attempt {connection_attempts})")
                logger.error(traceback.format_exc())
                # Reset registration state on connection failure
                registered = False
                await asyncio.sleep(backoff)
    
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
    
    async def heartbeat(self, websocket):
        """Send periodic heartbeats to keep connection alive"""
        try:
            while self.running:
                try:
                    await websocket.send(json.dumps({
                        "type": "ping",
                        "timestamp": datetime.now().isoformat()
                    }))
                    logger.debug("Sent heartbeat ping")
                except Exception as e:
                    logger.error(f"Error sending heartbeat: {e}")
                    break
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
        except asyncio.CancelledError:
            logger.info("Heartbeat task cancelled")
        except Exception as e:
            logger.error(f"Error in heartbeat task: {e}")
            
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
        asyncio.run(run_memory_connector())
    except KeyboardInterrupt:
        logger.info("Memory connector stopped by user")
    except Exception as e:
        logger.error(f"Error running memory connector: {e}")
        logger.error(traceback.format_exc())

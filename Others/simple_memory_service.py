#!/usr/bin/env python3
"""
Simple Memory Service
A standalone memory service that doesn't rely on relative imports
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import time
from collections import deque

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_service')

class SimpleMemory:
    """A simple memory system that stores contexts and messages"""
    
    def __init__(self, server_uri="ws://localhost:8765"):
        self.server_uri = server_uri
        self.running = True
        self.messages = deque(maxlen=50)  # Store last 50 messages
        self.contexts = deque(maxlen=20)  # Store last 20 contexts
        self.sensor_data = {
            "screen": {},
            "process": {},
            "file": {}
        }
        
    def add_message(self, message):
        """Add a message to memory"""
        if isinstance(message, str):
            message = {"content": message, "timestamp": datetime.now().isoformat()}
        
        self.messages.append(message)
        logger.info(f"Added message to memory: {message.get('content', '')[:50]}...")
        
    def add_context(self, context):
        """Add context to memory"""
        if not isinstance(context, dict):
            context = {"data": context, "timestamp": datetime.now().isoformat()}
            
        self.contexts.append(context)
        logger.info(f"Added context to memory")
        
    def get_recent_messages(self, count=5):
        """Get recent messages"""
        return list(self.messages)[-count:]
    
    def get_recent_contexts(self, count=3):
        """Get recent contexts"""
        return list(self.contexts)[-count:]
    
    def update_sensor_data(self, sensor_type, data):
        """Update sensor data"""
        self.sensor_data[sensor_type] = data
        logger.info(f"Updated {sensor_type} sensor data")
    
    def get_combined_context(self):
        """Get a combined context with all data"""
        return {
            "messages": list(self.messages),
            "contexts": list(self.contexts),
            "sensor_data": self.sensor_data,
            "timestamp": datetime.now().isoformat()
        }
        
    async def connect_to_server(self):
        """Connect to the bridge server and handle messages"""
        while self.running:
            try:
                async with websockets.connect(self.server_uri) as websocket:
                    logger.info(f"Connected to bridge server at {self.server_uri}")
                    
                    # Process initial welcome message
                    response = await websocket.recv()
                    data = json.loads(response)
                    logger.info(f"Received from server: {data.get('type')}")
                    
                    # Send identification
                    await websocket.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "memory_service",
                            "version": "1.0.0",
                            "capabilities": ["context_storage", "message_storage"]
                        }
                    }))
                    
                    # Main message handling loop
                    while self.running:
                        try:
                            # Receive messages from server
                            message = await websocket.recv()
                            data = json.loads(message)
                            
                            # Process different message types
                            msg_type = data.get('type')
                            logger.info(f"Received message type: {msg_type}")
                            
                            if msg_type == 'sensor_data':
                                # Update sensor data in memory
                                payload = data.get('payload', {})
                                if 'screen' in payload:
                                    self.update_sensor_data('screen', payload['screen'])
                                if 'processes' in payload:
                                    self.update_sensor_data('process', {
                                        'processes': payload['processes'],
                                        'timestamp': datetime.now().isoformat()
                                    })
                                if 'files' in payload:
                                    self.update_sensor_data('file', {
                                        'files': payload['files'],
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    
                            elif msg_type == 'message':
                                # Store message in memory
                                message_content = data.get('payload', {})
                                self.add_message(message_content)
                                
                                # Send acknowledgment
                                await websocket.send(json.dumps({
                                    "type": "message_stored",
                                    "payload": {
                                        "success": True,
                                        "message_id": message_content.get('id', 'unknown'),
                                        "timestamp": datetime.now().isoformat()
                                    }
                                }))
                                
                            elif msg_type == 'context_request':
                                # Generate and send context
                                context = self.get_combined_context()
                                
                                await websocket.send(json.dumps({
                                    "type": "context_response",
                                    "payload": context,
                                    "timestamp": datetime.now().isoformat()
                                }))
                                logger.info(f"Sent context response")
                            
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            logger.error(traceback.format_exc())
                
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to bridge server failed: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
                
    async def run(self):
        """Main method to run the memory service"""
        logger.info("Starting memory service")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/memory_service.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Connect to server
        await self.connect_to_server()

# Function to run the memory service
async def run_memory_service():
    memory = SimpleMemory()
    await memory.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_memory_service())
    except KeyboardInterrupt:
        logger.info("Memory service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running memory service: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
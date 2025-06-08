#!/usr/bin/env python3
"""
Memory System
Manages short-term, long-term, and contextual memory with automatic data collection.
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
import psutil

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_system')

class MemorySystem:
    """Memory system that manages different types of memory and sensor data."""
    
    def __init__(self, memory_file="memory/memory_state.json", server_uri="ws://localhost:8765"):
        """Initialize the memory system."""
        self.memory_file = memory_file
        self.server_uri = server_uri
        self.running = True
        self.memory_state = None
        self.initialized = False
        
        # Initialize memory components
        self.short_term_memory = []
        self.long_term_memory = []
        self.context_memory = {
            'current_context': {},
            'application_context': {},
            'sensor_data': {
                'screen': {},
                'process': {},
                'file': {}
            },
            'activities': [],
            'relationships': {},
            'by_timestamp': {}
        }
        
        # Initialize sensor data storage
        self._sensor_data_storage = {
            'screen': {},
            'process': {},
            'file': {},
            'other': {}
        }
        
        # Initialize sensors
        self.screen_sensor = None
        self.process_sensor = None
        self.file_sensor = None
        
        # Initialize WebSocket connection
        self.ws = None
        
        logger.info("Memory system initialized")
    
    def load_memory(self):
        """Load memory state from file or create new if needed."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    logger.info("Memory state loaded successfully")
                    return data
            else:
                logger.warning("Memory state file not found, creating new")
                # Create new memory state
                return {
                    "version": "1.0",
                    "last_update": datetime.now().isoformat(),
                    "context": {},
                    "short_term": [],
                    "long_term": [],
                    "sensor_data": {
                        "screen": {},
                        "process": {},
                        "file": {}
                    }
                }
        except Exception as e:
            logger.error(f"Error loading memory state: {e}")
            logger.error(traceback.format_exc())
            return {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {},
                "short_term": [],
                "long_term": [],
                "sensor_data": {
                    "screen": {},
                    "process": {},
                    "file": {}
                }
            }
    
    def save_memory(self):
        """Save current memory state to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            
            # Prepare memory state
            memory_state = {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": self.context_memory,
                "short_term": self.short_term_memory,
                "long_term": self.long_term_memory,
                "sensor_data": self._sensor_data_storage
            }
            
            # Save to file
            with open(self.memory_file, 'w') as f:
                json.dump(memory_state, f, indent=2)
            
            logger.info("Memory state saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def initialize(self):
        """Initialize the memory system with automatic sensor data collection."""
        try:
            logger.info("Initializing memory system...")
            
            # Load existing memory state
            self.memory_state = self.load_memory()
            self.short_term_memory = self.memory_state.get('short_term', [])
            self.long_term_memory = self.memory_state.get('long_term', [])
            self.context_memory = self.memory_state.get('context', {})
            self._sensor_data_storage = self.memory_state.get('sensor_data', {})
            
            logger.info(f"  - Found {len(self.short_term_memory)} short-term memory items")
            logger.info(f"  - Found {len(self.long_term_memory)} long-term memory items")
            logger.info(f"  - Found {len(self.context_memory)} context memory items")
            logger.info(f"  - Loaded sensor data storage with {len(self._sensor_data_storage)} items")
            
            # Initialize sensors
            logger.info("Initializing sensors...")
            try:
                from sensors.screen_sensor import ScreenSensor
                from sensors.process_sensor import ProcessSensor
                from sensors.file_sensor import FileSensor
                
                self.screen_sensor = ScreenSensor()
                self.process_sensor = ProcessSensor()
                self.file_sensor = FileSensor()
                
                logger.info("Sensors initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing sensors: {e}")
                logger.error(traceback.format_exc())
                return False
            
            # Start sensor data collection
            logger.info("Starting sensor data collection...")
            asyncio.create_task(self._collect_sensor_data())
            
            # Start periodic memory cleanup
            logger.info("Starting periodic memory cleanup...")
            asyncio.create_task(self._periodic_cleanup())
            
            # Start WebSocket server
            logger.info("Starting WebSocket server...")
            asyncio.create_task(self.start_websocket_server())
            
            self.initialized = True
            logger.info("Memory system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _collect_sensor_data(self):
        """Collect data from all sensors periodically."""
        while self.running:
            try:
                # Collect screen data
                if self.screen_sensor:
                    screen_data = await self.screen_sensor.get_data()
                    self._sensor_data_storage['screen'] = screen_data
                
                # Collect process data
                if self.process_sensor:
                    process_data = await self.process_sensor.get_data()
                self._sensor_data_storage['process'] = process_data
                
                # Collect file data
                if self.file_sensor:
                    file_data = await self.file_sensor.get_data()
                self._sensor_data_storage['file'] = file_data
                
                # Update context memory with sensor data
                self.context_memory['sensor_data'] = self._sensor_data_storage
                
                # Save memory state
                self.save_memory()
                
                # Wait before next collection
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error collecting sensor data: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)
    
    async def _periodic_cleanup(self):
        """Periodically clean up old memory entries."""
        while self.running:
            try:
                # Clean up old short-term memory
                current_time = datetime.now()
                self.short_term_memory = [
                    item for item in self.short_term_memory
                    if (current_time - datetime.fromisoformat(item['timestamp'])).days < 7
                ]
                
                # Clean up old sensor data
                for sensor_type in self._sensor_data_storage:
                    if 'timestamp' in self._sensor_data_storage[sensor_type]:
                        sensor_time = datetime.fromisoformat(self._sensor_data_storage[sensor_type]['timestamp'])
                        if (current_time - sensor_time).days > 1:
                            self._sensor_data_storage[sensor_type] = {}
                
                # Save memory state
                self.save_memory()
                
                # Wait before next cleanup
                await asyncio.sleep(3600)  # Clean up every hour
                
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(3600)
    
    async def start_websocket_server(self):
        """Start the WebSocket server for client connections."""
        async def handle_client(websocket):
            """Handle client WebSocket connections."""
            try:
                logger.info(f"New client connected: {websocket.remote_address}")
                while True:
                    # Get current metrics
                    metrics = {
                        "memory_usage": len(self.short_term_memory),
                        "long_term_memory": len(self.long_term_memory),
                        "active_tasks": len(self.context_memory.get("activities", [])),
                        "cpu_usage": psutil.cpu_percent(),
                        "memory_usage_percent": psutil.virtual_memory().percent,
                        "disk_usage": psutil.disk_usage('/').percent,
                        "details": f"Memory items: {len(self.short_term_memory)} short-term, {len(self.long_term_memory)} long-term"
                    }
                    
                    # Send metrics to client
                    await websocket.send(json.dumps(metrics))
                    await asyncio.sleep(1)  # Update every second
                    
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client disconnected: {websocket.remote_address}")
            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                logger.error(traceback.format_exc())
        
        # Start WebSocket server
        server = await websockets.serve(handle_client, "localhost", 8765)
        logger.info("WebSocket server started on ws://localhost:8765")
        return server
    
    async def stop(self):
        """Stop the memory system."""
        self.running = False
        if self.ws:
            await self.ws.close()
        self.save_memory()
        logger.info("Memory system stopped")

async def main():
    """Main function to run the memory system."""
    try:
        # Initialize memory system
        memory_system = MemorySystem() 
        await memory_system.initialize()
        
        # Keep the system running
        while memory_system.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Memory system stopped by user")
    except Exception as e:
        logger.error(f"Error in memory system: {e}")
        logger.error(traceback.format_exc())
    finally:
        if 'memory_system' in locals():
            await memory_system.stop()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 
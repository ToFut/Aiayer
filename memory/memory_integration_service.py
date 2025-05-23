#!/usr/bin/env python3
"""
Memory Integration Service
Bridges sensors with memory system for real-time data flow.
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.client import WebSocketClientProtocol

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/integration_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import memory components
try:
    # Try relative imports first
    from memory.safe_json import safe_load, safe_dump
    from memory.conscious_memory import ConsciousMemory
except ImportError:
    try:
        # Try direct imports
        from safe_json import safe_load, safe_dump
        from conscious_memory import ConsciousMemory
    except ImportError:
        # Create minimal fallbacks
        logger.warning("Using fallback JSON functions")
        import json
        def safe_load(content, default=None):
            try:
                return json.loads(content) if isinstance(content, str) else json.load(content)
            except:
                return default or {}
        def safe_dump(data, indent=2):
            try:
                return json.dumps(data, indent=indent)
            except:
                return "{}"
        
        # Minimal ConsciousMemory fallback
        class ConsciousMemory:
            def __init__(self, llm_provider=None, memory_system=None):
                self.llm_provider = llm_provider
                self.memory_system = memory_system
                logger.info("Using fallback ConsciousMemory")
            def add_screen_data(self, data):
                logger.info(f"Screen data: {data.get('timestamp')} - {data.get('screen_text', '')[:100]}...")
            def add_process_data(self, data):
                logger.info(f"Process data: {data.get('timestamp')} - {len(data.get('active_processes', []))} apps")
            def generate_insights(self):
                logger.debug("Generated insights")

class MemoryIntegrationService:
    """Service that integrates sensor data with memory system."""
    
    def __init__(self):
        self.bridge_uri = "ws://localhost:8765"
        self.client_type = "memory_integration"
        self.websocket = None
        self.conscious_memory = None
        self.memory_state_file = "memory/memory_state.json"
        self.running = False
        
    async def start(self):
        """Start the memory integration service."""
        logger.info("Starting Memory Integration Service...")
        
        # Initialize conscious memory
        try:
            self.conscious_memory = ConsciousMemory()
            logger.info("Conscious memory initialized")
        except Exception as e:
            logger.error(f"Failed to initialize conscious memory: {e}")
            return False
            
        self.running = True
        
        # Connect to bridge server
        while self.running:
            try:
                await self.connect_and_run()
            except Exception as e:
                logger.error(f"Service error: {e}")
                if self.running:
                    logger.info("Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                    
    async def connect_and_run(self):
        """Connect to bridge server and process messages."""
        try:
            logger.info(f"Connecting to bridge server: {self.bridge_uri}")
            async with websockets.connect(self.bridge_uri) as websocket:
                self.websocket = websocket
                
                # Register with bridge server
                await self.register()
                
                # Process incoming messages
                async for message in websocket:
                    await self.process_message(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to bridge server closed")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            
    async def register(self):
        """Register with the bridge server."""
        registration = {
            "type": "register",
            "client_type": self.client_type,
            "capabilities": ["memory_integration", "sensor_data_processing"],
            "version": "1.0.0"
        }
        
        await self.websocket.send(json.dumps(registration))
        logger.info("Registered with bridge server")
        
    async def process_message(self, message: str):
        """Process incoming messages from sensors."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "sensor_data":
                await self.handle_sensor_data(data)
            elif message_type == "connection_established":
                logger.info("Connection established with bridge server")
            else:
                logger.debug(f"Unhandled message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error("Failed to decode message as JSON")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    async def handle_sensor_data(self, data: Dict[str, Any]):
        """Handle sensor data and integrate with memory."""
        try:
            sensor_type = data.get("sensor_type")
            sensor_data = data.get("data", {})
            timestamp = data.get("timestamp", datetime.now().isoformat())
            
            logger.info(f"Processing {sensor_type} sensor data")
            
            # Update conscious memory
            if self.conscious_memory:
                await self.update_conscious_memory(sensor_type, sensor_data, timestamp)
                
            # Update memory state file
            await self.update_memory_state(sensor_type, sensor_data, timestamp)
            
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")
            
    async def update_conscious_memory(self, sensor_type: str, data: Dict[str, Any], timestamp: str):
        """Update conscious memory with sensor data."""
        try:
            if sensor_type == "screen":
                # Process screen data
                screen_info = {
                    "timestamp": timestamp,
                    "screen_text": data.get("screen_text", ""),
                    "image_hash": data.get("image_hash", ""),
                    "screen_size": data.get("screen_size", [0, 0]),
                    "source_file": data.get("source_file", "")
                }
                self.conscious_memory.add_screen_data(screen_info)
                
            elif sensor_type == "process":
                # Process process data
                process_info = {
                    "timestamp": timestamp,
                    "active_window": data.get("active_window", ""),
                    "active_app": data.get("active_app", ""),
                    "active_processes": data.get("active_processes", []),
                    "window_history": data.get("window_history", [])
                }
                self.conscious_memory.add_process_data(process_info)
                
            # Generate insights
            self.conscious_memory.generate_insights()
            
        except Exception as e:
            logger.error(f"Error updating conscious memory: {e}")
            
    async def update_memory_state(self, sensor_type: str, data: Dict[str, Any], timestamp: str):
        """Update memory state file with sensor data."""
        try:
            # Load current state
            memory_state = safe_load(open(self.memory_state_file).read() if os.path.exists(self.memory_state_file) else "{}", {})
            
            # Update with new data
            memory_state["last_update"] = timestamp
            memory_state["version"] = "1.0"
            
            # Initialize context if needed
            if "context" not in memory_state:
                memory_state["context"] = {}
                
            # Initialize sensor_data if needed
            if "sensor_data" not in memory_state:
                memory_state["sensor_data"] = {}
                
            # Update sensor data
            memory_state["sensor_data"][sensor_type] = data
            
            # Update context based on sensor type
            if sensor_type == "process":
                memory_state["context"]["active_window"] = data.get("active_window", "")
                memory_state["context"]["active_app"] = data.get("active_app", "")
                memory_state["context"]["active_apps"] = data.get("active_processes", [])[:5]  # Top 5
                memory_state["context"]["window_history"] = data.get("window_history", [])[-10:]  # Last 10
                
            elif sensor_type == "screen":
                memory_state["context"]["screen_text"] = data.get("screen_text", "")[:1000]  # Limit size
                
            # Save updated state
            with open(self.memory_state_file, 'w') as f:
                f.write(safe_dump(memory_state, indent=2))
                
            logger.debug(f"Updated memory state with {sensor_type} data")
            
        except Exception as e:
            logger.error(f"Error updating memory state: {e}")
            
    async def stop(self):
        """Stop the service."""
        logger.info("Stopping Memory Integration Service...")
        self.running = False
        if self.websocket:
            await self.websocket.close()

async def main():
    """Main entry point."""
    service = MemoryIntegrationService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main())
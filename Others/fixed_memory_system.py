#!/usr/bin/env python3
import json
import logging
import os
import sys
import traceback
import asyncio
import websockets
from datetime import datetime

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
    def __init__(self, memory_file="memory/memory_state.json", server_uri="ws://localhost:8765"):
        self.memory_file = memory_file
        self.server_uri = server_uri
        self.running = True
        self.memory_state = None
        self.context_data = {
            "processes": [],
            "screen": {},
            "files": []
        }
        
    def load_memory(self):
        """Load memory state from file or create new if needed"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                logger.info("Memory state loaded successfully")
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load memory state: {e}, creating new")
            # Create new memory state
            return {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {},
                "short_term": [],
                "long_term": []
            }
    
    def save_memory(self):
        """Save current memory state to file"""
        if not self.memory_state:
            return False
            
        try:
            # Update timestamp
            self.memory_state["last_update"] = datetime.now().isoformat()
            
            # Update context with latest sensor data
            self.memory_state["context"] = {
                "last_update": datetime.now().isoformat(),
                "processes": self.context_data.get("processes", [])[:5],  # Top 5 processes
                "active_window": self.context_data.get("screen", {}).get("window_title", ""),
                "active_app": self.context_data.get("screen", {}).get("active_app", ""),
                "recent_files": self.context_data.get("files", [])[:3]  # Top 3 recent files
            }
            
            # Save to file
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_state, f, indent=2)
            
            logger.debug("Memory state saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def connect_to_server(self):
        """Connect to the bridge server to receive context updates"""
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
                            "client": "memory_system",
                            "version": "1.0.0",
                            "capabilities": ["context_tracking", "memory_persistence"]
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
                            
                            if msg_type == 'sensor_data':
                                # Update context data from sensors
                                payload = data.get('payload', {})
                                if "processes" in payload:
                                    self.context_data["processes"] = payload["processes"]
                                if "screen" in payload:
                                    self.context_data["screen"] = payload["screen"]
                                if "files" in payload:
                                    self.context_data["files"] = payload["files"]
                                
                                # Update memory with new context
                                self.save_memory()
                            
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
    
    async def periodic_save(self):
        """Periodically save memory state"""
        while self.running:
            try:
                self.save_memory()
            except Exception as e:
                logger.error(f"Error in periodic save: {e}")
            
            # Sleep for 30 seconds
            await asyncio.sleep(30)
    
    async def run(self):
        """Main method to run the memory system"""
        logger.info("Starting memory system")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/memory_system.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Load initial memory state
        self.memory_state = self.load_memory()
        
        # Create tasks
        server_task = asyncio.create_task(self.connect_to_server())
        save_task = asyncio.create_task(self.periodic_save())
        
        # Wait for both tasks
        try:
            await asyncio.gather(server_task, save_task)
        except asyncio.CancelledError:
            logger.info("Memory system tasks cancelled")
        finally:
            # Save memory state one last time
            self.save_memory()

# Function to run the memory system
async def run_memory_system():
    memory = MemorySystem()
    await memory.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_memory_system())
    except KeyboardInterrupt:
        logger.info("Memory system stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running memory system: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

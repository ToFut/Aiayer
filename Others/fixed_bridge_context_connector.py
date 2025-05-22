#!/usr/bin/env python3
"""
Fixed Bridge Context Connector

Enhanced bridge between sensors and memory system to ensure context updates.
Explicitly triggers context updates and formats sensor data correctly for memory.
"""
import asyncio
import websockets
import json
import logging
import os
import sys
import time
from datetime import datetime
import aiohttp

# Setup logging
os.makedirs('logs/bridge', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bridge/context_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('context_bridge_connector')

# Configuration
BRIDGE_WS_URI = "ws://localhost:8766"
MEMORY_API_URL = "http://localhost:8767/api/memory"
CONTEXT_FILE = "memory/last_context.json"

async def update_context_file(sensor_type, data):
    """Update last_context.json file with sensor data directly"""
    try:
        # Load current context
        context = {}
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r') as f:
                context = json.load(f)
        
        # Update timestamp
        context["timestamp"] = int(time.time())
        
        # Update based on sensor type
        if sensor_type == "process":
            context["active_window"] = data.get("active_window", "")
            context["active_app"] = data.get("active_app", "")
            context["active_apps"] = data.get("active_apps", [])
            
            # Format active_apps if it's not a list
            if isinstance(context["active_apps"], dict):
                context["active_apps"] = list(context["active_apps"].values())
            
            # Extract just the names if they're in dict format
            if context["active_apps"] and isinstance(context["active_apps"][0], dict):
                context["active_apps"] = [app.get("name", "") for app in context["active_apps"]]
                
            # Track window history
            if "window_history" not in context:
                context["window_history"] = []
            
            # Add current window to history if different from last one
            if context["active_window"] and (not context["window_history"] or context["active_window"] != context["window_history"][0]):
                context["window_history"].insert(0, context["active_window"])
                # Keep only the 10 most recent windows
                context["window_history"] = context["window_history"][:10]
                
        elif sensor_type == "screen":
            # Update screen text field
            context["screen_text"] = data.get("screen_text", data.get("text", ""))
        
        # Save updated context
        with open(CONTEXT_FILE, 'w') as f:
            json.dump(context, f, indent=2)
        
        logger.info(f"✅ Updated last_context.json with {sensor_type} data")
        return context
    except Exception as e:
        logger.error(f"Error updating context file: {e}")
        return None

async def update_memory_system(context):
    """Update memory system via API call"""
    try:
        if not context:
            return False
            
        # Call memory API endpoint to update context
        async with aiohttp.ClientSession() as session:
            payload = {
                "type": "context_update",
                "data": context,
                "timestamp": datetime.now().isoformat()
            }
            
            async with session.post(MEMORY_API_URL + "/update_context", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Memory system updated via API: {result.get('status')}")
                    return True
                else:
                    logger.warning(f"Memory API returned status {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Error calling memory API: {e}")
        return False

async def fetch_active_context():
    """Fetch the current active context"""
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error fetching active context: {e}")
        return None

async def connect_to_bridge():
    """Connect to the bridge server and process data"""
    retry_delay = 5  # seconds
    
    while True:
        try:
            logger.info(f"Connecting to bridge server at {BRIDGE_WS_URI}")
            
            async with websockets.connect(BRIDGE_WS_URI) as websocket:
                logger.info("Connected to bridge server")
                
                # Register as a memory client
                await websocket.send(json.dumps({
                    "type": "register",
                    "client_type": "memory",
                    "version": "1.0.0",
                    "capabilities": ["context_management"]
                }))
                
                # Wait for registration confirmation
                response = await websocket.recv()
                data = json.loads(response)
                
                if data.get("type") == "registration_confirmed":
                    logger.info("Registration confirmed by bridge server")
                else:
                    logger.warning(f"Unexpected registration response: {data.get('type')}")
                
                # Process incoming messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        
                        if msg_type == "sensor_data":
                            # Extract sensor data
                            sensor_type = data.get("sensor_type", "")
                            payload = data.get("payload", {})
                            
                            if sensor_type and payload:
                                # Update context file first
                                updated_context = await update_context_file(sensor_type, payload)
                                
                                # Then try to update memory system via API
                                await update_memory_system(updated_context)
                                
                                # Send acknowledgment
                                await websocket.send(json.dumps({
                                    "type": "ack",
                                    "message": f"Context updated with {sensor_type} data",
                                    "timestamp": datetime.now().isoformat()
                                }))
                            else:
                                logger.warning("Received invalid sensor data")
                        
                        elif msg_type == "pong":
                            # Just a heartbeat response
                            pass
                        
                        elif msg_type == "get_context":
                            # Someone is requesting the current context
                            context = await fetch_active_context()
                            await websocket.send(json.dumps({
                                "type": "context",
                                "data": context,
                                "timestamp": datetime.now().isoformat()
                            }))
                        
                        else:
                            logger.debug(f"Received message type: {msg_type}")
                        
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON received from bridge")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
        
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
            logger.warning(f"Connection to bridge server lost: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info(f"Retrying in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)

async def periodic_context_update():
    """Periodically check and update context file"""
    while True:
        try:
            # Fetch active context
            context = await fetch_active_context()
            if context:
                # Send to memory API
                await update_memory_system(context)
                logger.info("Performed periodic context update")
            
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in periodic update: {e}")
            await asyncio.sleep(30)

async def main():
    """Main function to run the bridge context connector"""
    try:
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/bridge_context_connector.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info("Starting bridge context connector")
        
        # Initialize context file if it doesn't exist
        if not os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'w') as f:
                json.dump({
                    "timestamp": int(time.time()),
                    "active_window": "",
                    "active_app": "",
                    "active_apps": [],
                    "window_history": [],
                    "screen_text": ""
                }, f, indent=2)
        
        # Start tasks
        bridge_task = asyncio.create_task(connect_to_bridge())
        update_task = asyncio.create_task(periodic_context_update())
        
        # Wait for tasks to complete (they should run indefinitely)
        await asyncio.gather(bridge_task, update_task)
    
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Add aiohttp to requirements
        try:
            import aiohttp
        except ImportError:
            logger.info("Installing required dependencies...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp"])
            import aiohttp
            
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bridge context connector stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
#!/usr/bin/env python3
"""
Sensor Connection Utility for Agent-Based LLM WebSocket Server
This script ensures proper connection between sensors and the memory system
"""
import asyncio
import argparse
import logging
import os
import json
import sys
import time
import websockets
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/connect_sensors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('connect_sensors')

# Constants
WS_URL = "ws://localhost:8765"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
SCREEN_CACHE_DIR = os.path.join(CACHE_DIR, "screen_sensor")
PROCESS_CACHE_DIR = os.path.join(CACHE_DIR, "process_sensor")
FILE_CACHE_DIR = os.path.join(CACHE_DIR, "file_sensor")

# Ensure cache directories exist
os.makedirs(SCREEN_CACHE_DIR, exist_ok=True)
os.makedirs(PROCESS_CACHE_DIR, exist_ok=True)
os.makedirs(FILE_CACHE_DIR, exist_ok=True)

# Cache paths
SCREEN_CACHE_PATH = os.path.join(SCREEN_CACHE_DIR, "screen_cache.json")
LAST_SCREEN_PATH = os.path.join(SCREEN_CACHE_DIR, "last_screen.json")
PROCESS_CACHE_PATH = os.path.join(PROCESS_CACHE_DIR, "process_cache.json")
LAST_FILE_PATH = os.path.join(FILE_CACHE_DIR, "last_file.json")

async def send_sensor_data(websocket, sensor_type, data):
    """Send sensor data to the WebSocket server"""
    try:
        message = {
            "type": "sensor_data",
            "payload": {
                "sensor_type": sensor_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(message))
        logger.info(f"Sent {sensor_type} sensor data to server")
        
        # Wait for acknowledgment
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("type") == "sensor_data_received":
            logger.info(f"Server acknowledged {sensor_type} sensor data")
            return True
        else:
            logger.warning(f"Unexpected response type: {response_data.get('type')}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending {sensor_type} sensor data: {e}")
        return False

def load_cache_file(file_path, default=None):
    """Load data from cache file or return default"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"Error loading cache file {file_path}: {e}")
        return default if default is not None else {}

async def connect_and_send_data(sensor_types, max_retries=5, retry_delay=2):
    """Connect to WebSocket server and send sensor data with retries"""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Connecting to WebSocket server at {WS_URL} (attempt {retry_count+1}/{max_retries})")
            
            # Try both localhost formats
            ws_urls = [
                WS_URL,
                WS_URL.replace("localhost", "127.0.0.1"),
                "ws://127.0.0.1:8765"
            ]
            
            connected = False
            websocket = None
            connect_error = None
            
            # Try each URL format
            for url in ws_urls:
                try:
                    websocket = await websockets.connect(url, ping_interval=None, close_timeout=5)
                    logger.info(f"Successfully connected to server at {url}")
                    connected = True
                    break
                except Exception as e:
                    connect_error = e
                    logger.warning(f"Failed to connect to {url}: {e}")
            
            if not connected:
                raise connect_error if connect_error else Exception("Failed to connect to any WebSocket URL")
            
            logger.info("Connected to WebSocket server")
            
            # Send connection established message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "sensor_connector",
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            try:
                # Receive server ready message with timeout
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received: {response[:100]}...")
            except asyncio.TimeoutError:
                logger.warning("Timed out waiting for server response, continuing anyway...")
            
            # Send sensor data based on specified types
            if "screen" in sensor_types:
                # Load screen data from cache
                screen_data = load_cache_file(LAST_SCREEN_PATH)
                screen_cache = load_cache_file(SCREEN_CACHE_PATH, {"entries": []})
                
                # Ensure screen_data has all the expected fields
                if not screen_data:
                    screen_data = {
                        "timestamp": int(time.time()),
                        "screen_text": "SensAI Agent-Based WebSocket Server initialization screen."
                    }
                
                # Combine recent entries with current data
                combined_data = {
                    "current": screen_data,
                    "recent_entries": screen_cache.get("entries", [])[-5:],
                    "window": screen_data.get("window", "Unknown"),
                    "screen_content": screen_data.get("screen_text", screen_data.get("text", "")),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send screen data
                screen_content_length = len(combined_data.get('screen_content', ''))
                logger.info(f"Sending screen data, content length: {screen_content_length}")
                if screen_content_length == 0:
                    logger.warning("⚠️ Screen content is empty! Perception queries will not work correctly.")
                await send_sensor_data(websocket, "screen", combined_data)
            
            if "process" in sensor_types:
                # Load process data from cache
                process_data = load_cache_file(PROCESS_CACHE_PATH, {"processes": []})
                
                # Format process data
                formatted_data = {
                    "active_window": process_data.get("active_window", "Unknown"),
                    "active_app": process_data.get("active_app", "Unknown"),
                    "active_apps": [p.get("name") for p in process_data.get("processes", [])[:10]],
                    "window_history": process_data.get("window_history", []),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send process data
                logger.info(f"Sending process data with {len(formatted_data.get('active_apps', []))} active apps")
                await send_sensor_data(websocket, "process", formatted_data)
            
            if "file" in sensor_types:
                # Load file data from cache
                file_data = load_cache_file(LAST_FILE_PATH, {"files": []})
                
                # Format file data
                formatted_data = {
                    "recent_files": file_data.get("files", [])[-10:],
                    "current_file": file_data.get("current_file", {}),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send file data
                logger.info(f"Sending file data with {len(formatted_data.get('recent_files', []))} recent files")
                await send_sensor_data(websocket, "file", formatted_data)
                
            logger.info("Successfully sent all sensor data to memory system")
            await websocket.close()
            return True
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Error connecting to WebSocket server: {e}")
            
            if retry_count < max_retries:
                wait_time = retry_delay * retry_count
                logger.info(f"Retrying in {wait_time} seconds... (attempt {retry_count+1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to connect after {max_retries} attempts")
                return False
        
    return False

async def verify_memory_state():
    """Connect to server and check if memory has data"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URL} to verify memory state")
        
        async with websockets.connect(WS_URL) as websocket:
            logger.info("Connected to WebSocket server for verification")
            
            # Send connection established message
            await websocket.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client": "memory_verifier",
                    "version": "1.0.0",
                    "timestamp": datetime.now().isoformat()
                }
            }))
            
            # Receive server ready message
            await websocket.recv()
            
            # Request context update
            await websocket.send(json.dumps({
                "type": "context_request",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Receive context update
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "context_update":
                context = response_data.get("payload", {}).get("context", {})
                
                # Check if memory has data
                screen_content = context.get("screen_content", "")
                active_apps = context.get("active_apps", [])
                window = context.get("window", "Unknown")
                
                logger.info(f"Memory verification results:")
                logger.info(f"- Window: {window}")
                logger.info(f"- Active apps: {len(active_apps)} apps")
                logger.info(f"- Screen content: {len(screen_content)} chars")
                
                return {
                    "has_screen_content": bool(screen_content),
                    "has_active_apps": bool(active_apps),
                    "window_known": window != "Unknown",
                    "context": context
                }
            else:
                logger.warning(f"Unexpected response type: {response_data.get('type')}")
                return {
                    "has_screen_content": False,
                    "has_active_apps": False,
                    "window_known": False
                }
                
    except Exception as e:
        logger.error(f"Error verifying memory state: {e}")
        return {
            "has_screen_content": False,
            "has_active_apps": False,
            "window_known": False,
            "error": str(e)
        }

async def main():
    parser = argparse.ArgumentParser(description="Connect sensors to memory system")
    parser.add_argument(
        "--sensors", 
        nargs="+", 
        default=["screen", "process", "file"],
        help="Sensor types to connect (screen, process, file)"
    )
    parser.add_argument(
        "--verify", 
        action="store_true",
        help="Verify memory state after connecting sensors"
    )
    parser.add_argument(
        "--loop", 
        action="store_true",
        help="Run continuously to keep sending sensor data"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=10,
        help="Interval in seconds between data sends when in loop mode"
    )
    
    args = parser.parse_args()
    
    if args.loop:
        logger.info(f"Running in continuous mode with {args.interval}s interval")
        while True:
            try:
                success = await connect_and_send_data(args.sensors)
                
                if args.verify and success:
                    verification = await verify_memory_state()
                    if not verification.get("has_screen_content") and "screen" in args.sensors:
                        logger.warning("Memory system does not have screen content")
                    if not verification.get("has_active_apps") and "process" in args.sensors:
                        logger.warning("Memory system does not have active apps data")
                        
                logger.info(f"Waiting {args.interval} seconds before next update...")
                await asyncio.sleep(args.interval)
                
            except Exception as e:
                logger.error(f"Error in loop: {e}")
                await asyncio.sleep(5)  # Wait before retry
    else:
        # Single run mode
        success = await connect_and_send_data(args.sensors)
        
        if args.verify and success:
            verification = await verify_memory_state()
            
            if verification.get("has_screen_content"):
                logger.info("✅ Memory system has screen content")
            else:
                logger.warning("❌ Memory system does not have screen content")
                
            if verification.get("has_active_apps"):
                logger.info("✅ Memory system has active apps data")
            else:
                logger.warning("❌ Memory system does not have active apps data")
                
            if verification.get("window_known"):
                logger.info("✅ Memory system has window information")
            else:
                logger.warning("❌ Memory system does not have window information")
        
        logger.info("Completed sensor connection")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sensor connector stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)
#!/usr/bin/env python3
"""
Enhanced Process Sensor
Captures process data and sends it to the bridge server.
"""
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import websockets
from websockets.client import WebSocketClientProtocol
import psutil
import subprocess

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BRIDGE_SERVER_URI = "ws://localhost:8767"  # Connect to Real LLM Backend
CLIENT_TYPE = "process_sensor"
VERSION = "1.0.0"
CAPABILITIES = ["process_monitoring", "resource_usage"]

async def connect_to_bridge() -> Optional[WebSocketClientProtocol]:
    """Connect to the bridge server."""
    try:
        websocket = await websockets.connect(BRIDGE_SERVER_URI)
        logger.info("Connected to bridge server")
        return websocket
    except Exception as e:
        logger.error(f"Error connecting to bridge server: {e}")
        return None

async def register_with_bridge(websocket: WebSocketClientProtocol) -> bool:
    """Register with the bridge server."""
    try:
        # First, receive the welcome message
        welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        welcome_data = json.loads(welcome)
        logger.info(f"Received welcome: {welcome_data.get('type')}")
        
        # Send registration message
        registration_msg = {
            "type": "register",
            "client_type": CLIENT_TYPE,
            "version": VERSION,
            "capabilities": CAPABILITIES,
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send(json.dumps(registration_msg))
        logger.info("Sent registration message")
        
        # Wait for registration confirmation
        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        data = json.loads(response)
        
        if data.get("type") == "registration_success":
            logger.info(f"Registration successful: {data.get('message')}")
            return True
        elif data.get("type") == "registration_confirmed":
            logger.info(f"Registration confirmed as {data.get('payload', {}).get('client_type')}")
            return True
        else:
            logger.error(f"Unexpected response to registration: {data}")
            return False
            
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for registration confirmation")
        return False
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return False

def get_active_applications() -> List[Dict[str, Any]]:
    """Get list of currently running applications with rich context."""
    try:
        active_apps = []
        seen_names = set()
        
        # Get all running processes
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'create_time']):
            try:
                proc_info = proc.info
                name = proc_info['name']
                
                # Skip system processes and duplicates
                if name and name not in seen_names and not name.startswith('kernel') and name != 'launchd':
                    seen_names.add(name)
                    
                    # Categorize application type
                    app_type = categorize_application(name)
                    
                    active_apps.append({
                        'name': name,
                        'pid': proc_info['pid'],
                        'type': app_type,
                        'memory_mb': round(proc_info['memory_info'].rss / 1024 / 1024, 1) if proc_info['memory_info'] else 0,
                        'cpu_percent': round(proc_info['cpu_percent'] or 0, 1),
                        'create_time': proc_info['create_time']
                    })
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        # Sort by memory usage and return top 20
        active_apps.sort(key=lambda x: x['memory_mb'], reverse=True)
        return active_apps[:20]
        
    except Exception as e:
        logger.error(f"Error getting active applications: {e}")
        return []

def categorize_application(name: str) -> str:
    """Categorize application by name."""
    name_lower = name.lower()
    
    if any(browser in name_lower for browser in ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave']):
        return 'browser'
    elif any(dev in name_lower for dev in ['code', 'studio', 'intellij', 'pycharm', 'xcode', 'terminal']):
        return 'development'
    elif any(comm in name_lower for comm in ['slack', 'teams', 'zoom', 'meet', 'discord', 'mail', 'outlook']):
        return 'communication'
    elif any(prod in name_lower for prod in ['office', 'word', 'excel', 'powerpoint', 'docs', 'sheets', 'notion']):
        return 'productivity'
    elif any(media in name_lower for media in ['spotify', 'netflix', 'youtube', 'vlc', 'music', 'photos']):
        return 'media'
    else:
        return 'other'

def get_active_window_info() -> Dict[str, str]:
    """Get information about the currently active window (macOS specific)."""
    try:
        # Use AppleScript to get active window info
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            set frontWindow to name of front window of first application process whose frontmost is true
        end tell
        return frontApp & "|||" & frontWindow
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split('|||')
            return {
                'active_app': parts[0] if len(parts) > 0 else 'Unknown',
                'active_window': parts[1] if len(parts) > 1 else 'Unknown Window'
            }
    except Exception as e:
        logger.debug(f"Could not get active window info: {e}")
    
    return {'active_app': 'Unknown', 'active_window': 'Unknown Window'}

async def send_process_data(websocket: WebSocketClientProtocol):
    """Send enhanced process data to the bridge server."""
    try:
        # Get active applications with rich context
        active_apps = get_active_applications()
        
        # Get active window information
        window_info = get_active_window_info()
        
        # Create enhanced process data
        process_data = {
            "type": "sensor_data",
            "sensor_type": "process",
            "data": {
                    "timestamp": datetime.now().isoformat(),
                    "active_app": window_info['active_app'],
                    "active_window": window_info['active_window'],
                    "active_processes": active_apps,
                    "active_apps": [app['name'] for app in active_apps],
                    "system_info": {
                        "cpu_count": psutil.cpu_count(),
                        "memory_total_gb": round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 1),
                        "memory_used_percent": psutil.virtual_memory().percent
                    },
                    "is_significant_action": len(active_apps) > 0 or window_info['active_app'] != 'Unknown'
                }
        }
        
        # Also save to cache for direct integration
        cache_dir = "cache/process_sensor"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "process_cache.json")
        
        with open(cache_file, 'w') as f:
            json.dump(process_data["data"], f, indent=2)
        
        await websocket.send(json.dumps(process_data))
        logger.info(f"Sent enhanced process data: {len(active_apps)} apps, active: {window_info['active_app']}")
        
    except Exception as e:
        logger.error(f"Error sending process data: {e}")
        raise

async def send_heartbeat(websocket: WebSocketClientProtocol):
    """Send heartbeat to keep connection alive."""
    try:
        heartbeat_msg = {
            "type": "heartbeat",
            "payload": {
                "timestamp": datetime.now().isoformat()
            }
        }
        
        await websocket.send(json.dumps(heartbeat_msg))
        logger.debug("Sent heartbeat")
        
    except Exception as e:
        logger.error(f"Error sending heartbeat: {e}")
        raise

async def handle_messages(websocket: WebSocketClientProtocol):
    """Handle incoming messages from the bridge server."""
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "heartbeat_ack":
                    logger.debug("Received heartbeat acknowledgment")
                elif msg_type == "error":
                    logger.error(f"Received error: {data.get('payload', {}).get('message')}")
                else:
                    logger.warning(f"Received unexpected message type: {msg_type}")
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {message[:100]}...")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
        raise
    except Exception as e:
        logger.error(f"Error handling messages: {e}")
        raise

async def main():
    """Main function to run the process sensor."""
    while True:
        try:
            # Connect to bridge server
            websocket = await connect_to_bridge()
            if not websocket:
                logger.error("Failed to connect to bridge server")
                await asyncio.sleep(5)
                continue
            
            # Register with bridge server
            if not await register_with_bridge(websocket):
                logger.error("Failed to register with bridge server")
                await websocket.close()
                await asyncio.sleep(5)
                continue
            
            # Start message handler
            message_handler = asyncio.create_task(handle_messages(websocket))
            
            # Main loop
            while True:
                try:
                    # Send process data
                    await send_process_data(websocket)
                    
                    # Send heartbeat
                    await send_heartbeat(websocket)
                    
                    # Wait before next update (5 seconds for less frequent updates)
                    await asyncio.sleep(5)
                    
                except websockets.exceptions.ConnectionClosed:
                    logger.info("Connection closed during main loop")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    break
            
            # Clean up
            message_handler.cancel()
            try:
                await message_handler
            except asyncio.CancelledError:
                pass
            
            await websocket.close()
            logger.info("Disconnected from bridge server")
            
        except Exception as e:
            logger.error(f"Error in main: {e}")
        
        # Wait before reconnecting
        await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error running process sensor: {e}")
        sys.exit(1)

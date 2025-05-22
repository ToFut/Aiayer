#!/usr/bin/env python3
"""
Fix Screen Perception Issues
This script resolves the perception query issues by ensuring screen content is properly stored
and accessible to the memory system. It works by:
1. Establishing direct WebSocket connections using multiple connection strategies
2. Capturing current screen content
3. Sending it directly to both the WebSocket server and memory system
4. Verifying the data was successfully stored
"""
import asyncio
import websockets
import json
import logging
import os
import time
import base64
import io
import sys
import traceback
import socket
import random
from datetime import datetime
from PIL import Image
import mss

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fix_perception.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('fix_perception')

# Ensure directories exist
os.makedirs("cache/screen_sensor", exist_ok=True)
os.makedirs("memory", exist_ok=True)

# Constants
WEBSOCKET_PORT = 8765
MEMORY_FILE = "memory/memory_state.json"
SCREEN_CACHE_FILE = "cache/screen_sensor/screen_cache.json"
LAST_SCREEN_FILE = "cache/screen_sensor/last_screen.json"

async def capture_screen():
    """Capture the current screen"""
    try:
        with mss.mss() as sct:
            # Get primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Compress and convert to base64
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='JPEG', quality=70)
            img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            # Create screen data
            screen_data = {
                "timestamp": datetime.now().isoformat(),
                "image_data": img_base64,
                "screen_size": screenshot.size,
                "content": f"Screen capture {datetime.now().isoformat()} - {screenshot.size[0]}x{screenshot.size[1]}"
            }
            
            logger.info(f"Captured screen: {screenshot.size[0]}x{screenshot.size[1]}")
            return screen_data
            
    except Exception as e:
        logger.error(f"Error capturing screen: {e}")
        logger.error(traceback.format_exc())
        return None

def is_port_in_use(port, host='localhost'):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        if host == 'localhost':
            host = '127.0.0.1'
        return s.connect_ex((host, port)) == 0

async def connect_to_websocket():
    """Connect to WebSocket server with multiple strategies"""
    urls = [
        "ws://localhost:8765",
        "ws://127.0.0.1:8765",
        "ws://0.0.0.0:8765"
    ]
    
    # First check if port is in use
    if not is_port_in_use(WEBSOCKET_PORT):
        logger.warning(f"WebSocket port {WEBSOCKET_PORT} is not in use. Server may not be running.")
        return None
    
    # Try each URL
    for url in urls:
        try:
            logger.info(f"Connecting to {url}...")
            websocket = await asyncio.wait_for(
                websockets.connect(url, ping_interval=None, close_timeout=5),
                timeout=5
            )
            logger.info(f"Connected to {url}")
            return websocket
        except Exception as e:
            logger.warning(f"Failed to connect to {url}: {e}")
    
    logger.error("Failed to connect to WebSocket server")
    return None

def update_memory_state(screen_data):
    """Update memory state file with screen data"""
    try:
        # Load existing memory state or create new one
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                memory_state = json.load(f)
        else:
            memory_state = {
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
        
        # Make sure sensor_data and screen sections exist
        if "sensor_data" not in memory_state:
            memory_state["sensor_data"] = {}
        if "screen" not in memory_state["sensor_data"]:
            memory_state["sensor_data"]["screen"] = {}
        
        # Add screen data with timestamp as key
        timestamp = datetime.now().isoformat()
        memory_state["sensor_data"]["screen"][timestamp] = screen_data
        
        # Add screen content to context for immediate access
        if "context" not in memory_state:
            memory_state["context"] = {}
        
        # Ensure screen_content field exists in context
        memory_state["context"]["screen_content"] = screen_data.get("content", "")
        
        # Update last_update timestamp
        memory_state["last_update"] = timestamp
        
        # Save updated memory state
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory_state, f, indent=2)
        
        logger.info("Updated memory state with screen data")
        return True
    except Exception as e:
        logger.error(f"Error updating memory state: {e}")
        logger.error(traceback.format_exc())
        return False

def update_cache_files(screen_data):
    """Update screen cache files"""
    try:
        # Update screen cache file
        with open(SCREEN_CACHE_FILE, 'w') as f:
            json.dump(screen_data, f, indent=2)
        
        # Update last screen file
        with open(LAST_SCREEN_FILE, 'w') as f:
            json.dump(screen_data, f, indent=2)
        
        logger.info("Updated cache files with screen data")
        return True
    except Exception as e:
        logger.error(f"Error updating cache files: {e}")
        logger.error(traceback.format_exc())
        return False

async def send_screen_data_to_server(websocket, screen_data):
    """Send screen data to WebSocket server"""
    try:
        # Prepare message
        message = {
            "type": "sensor_data",
            "payload": {
                "sensor_type": "screen",
                "data": screen_data,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send message
        await websocket.send(json.dumps(message))
        logger.info("Sent screen data to WebSocket server")
        
        # Wait for acknowledgment
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            response_data = json.loads(response)
            logger.info(f"Received response: {response_data.get('type')}")
            return True
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for server response")
            return False
        
    except Exception as e:
        logger.error(f"Error sending screen data to server: {e}")
        logger.error(traceback.format_exc())
        return False

async def verify_memory_has_screen_content():
    """Verify memory state has screen content"""
    try:
        if not os.path.exists(MEMORY_FILE):
            logger.error("Memory state file not found")
            return False
            
        with open(MEMORY_FILE, 'r') as f:
            memory_state = json.load(f)
        
        # Check for screen content in context
        if "context" in memory_state and "screen_content" in memory_state["context"]:
            content = memory_state["context"]["screen_content"]
            if content and len(content) > 0:
                logger.info(f"Memory has screen content ({len(content)} chars)")
                print(f"✅ Memory has screen content ({len(content)} chars)")
                return True
            else:
                logger.warning("Memory has empty screen content")
                print("❌ Memory has empty screen content")
                return False
        
        # Check for screen data in sensor_data section
        if "sensor_data" in memory_state and "screen" in memory_state["sensor_data"]:
            screen_entries = memory_state["sensor_data"]["screen"]
            if screen_entries:
                logger.info(f"Memory has {len(screen_entries)} screen entries")
                print(f"✅ Memory has {len(screen_entries)} screen entries")
                return True
            else:
                logger.warning("Memory has no screen entries")
                print("❌ Memory has no screen entries")
                return False
                
        logger.warning("Memory missing screen content and entries")
        print("❌ Memory missing screen content and entries")
        return False
        
    except Exception as e:
        logger.error(f"Error verifying memory: {e}")
        logger.error(traceback.format_exc())
        return False

async def test_perception_query(websocket):
    """Test perception query by sending a query message"""
    if not websocket:
        logger.error("No WebSocket connection for perception query test")
        return False
        
    try:
        # Prepare query message
        message = {
            "type": "user_interaction",
            "payload": {
                "type": "query",
                "query": "what am I seeing?",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send query
        logger.info("Sending perception query: 'what am I seeing?'")
        print("ℹ️ Sending perception query: 'what am I seeing?'")
        await websocket.send(json.dumps(message))
        
        # Wait for response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            response_data = json.loads(response)
            
            if response_data.get("type") == "error":
                logger.error(f"Received error response: {response_data.get('error')}")
                print(f"❌ Received error: {response_data.get('error')}")
                return False
                
            logger.info(f"Received response type: {response_data.get('type')}")
            print(f"✅ Received response type: {response_data.get('type')}")
            return True
            
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for perception query response")
            print("❌ Timeout waiting for response")
            return False
            
    except Exception as e:
        logger.error(f"Error testing perception query: {e}")
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    print("\n=== Screen Perception Fix ===")
    print("Fixing screen content for perception queries")
    print("==================================\n")
    
    # Step 1: Capture screen
    print("Step 1: Capturing screen content...")
    screen_data = await capture_screen()
    if not screen_data:
        print("❌ Failed to capture screen content")
        return False
    print("✅ Screen captured successfully")
    
    # Step 2: Update cache files
    print("\nStep 2: Updating cache files...")
    if update_cache_files(screen_data):
        print("✅ Cache files updated successfully")
    else:
        print("❌ Failed to update cache files")
    
    # Step 3: Update memory state directly
    print("\nStep 3: Updating memory state directly...")
    if update_memory_state(screen_data):
        print("✅ Memory state updated successfully")
    else:
        print("❌ Failed to update memory state")
    
    # Step 4: Connect to WebSocket server
    print("\nStep 4: Connecting to WebSocket server...")
    websocket = await connect_to_websocket()
    if not websocket:
        print("❌ Failed to connect to WebSocket server")
        print("\nVerifying memory has screen content (direct method only)...")
        await verify_memory_has_screen_content()
        return
    print("✅ Connected to WebSocket server")
    
    # Step 5: Send screen data to server
    print("\nStep 5: Sending screen data to server...")
    server_success = await send_screen_data_to_server(websocket, screen_data)
    if server_success:
        print("✅ Screen data sent to server successfully")
    else:
        print("❌ Failed to send screen data to server")
    
    # Step 6: Verify memory has screen content
    print("\nStep 6: Verifying memory has screen content...")
    await verify_memory_has_screen_content()
    
    # Step 7: Wait a moment for processing
    print("\nStep 7: Waiting for server to process data...")
    await asyncio.sleep(2)
    
    # Step 8: Test perception query
    print("\nStep 8: Testing perception query...")
    await test_perception_query(websocket)
    
    # Clean up
    if websocket:
        await websocket.close()
    
    print("\n=== Fix Complete ===")
    print("The screen perception system should now be working correctly.")
    print("You can test it by asking 'what am I seeing?' in the chat interface.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ Fatal error: {e}")
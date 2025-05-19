#!/usr/bin/env python3
"""
Simplified Overlay Bridge Connector
Connects to WebSocket server and provides overlay functionality
"""
import asyncio
import websockets
import json
import logging
import signal
import sys
import time
import threading
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

class SimpleOverlayBridge:
    """A simplified bridge to connect the WebSocket server to the overlay UI"""
    
    def __init__(self, ws_port=8767, overlay_port=8765):
        self.ws_port = ws_port  # Port for connecting to WebSocket server
        self.overlay_port = overlay_port  # Port for serving overlay UI
        self.clients = set()  # Connected overlay clients
        self.server = None
        self.running = False
        self.ws_client = None
        self.reconnect_delay = 5  # seconds between reconnection attempts
        
    async def start_server(self):
        """Start the WebSocket server for overlay clients"""
        try:
            self.server = await websockets.serve(
                self.handle_client,
                "localhost",
                self.overlay_port
            )
            logger.info(f"Overlay server started on port {self.overlay_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start overlay server: {e}")
            return False
            
    async def handle_client(self, websocket, path):
        """Handle connections from overlay UI clients"""
        try:
            client_id = id(websocket)
            self.clients.add(websocket)
            logger.info(f"Overlay client connected: {client_id}")
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "Connected to overlay bridge"
            }))
            
            # Main client message loop
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.debug(f"Received from client: {data}")
                    
                    # Echo message back
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data
                    }))
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {message}")
                except Exception as e:
                    logger.error(f"Error processing client message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Overlay client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client connection: {e}")
        finally:
            self.clients.remove(websocket)
            
    async def connect_to_ws_server(self):
        """Connect to the WebSocket server"""
        while self.running:
            try:
                logger.info(f"Connecting to WebSocket server at ws://localhost:{self.ws_port}")
                async with websockets.connect(f"ws://localhost:{self.ws_port}") as websocket:
                    self.ws_client = websocket
                    logger.info("Connected to WebSocket server")
                    
                    # Process messages from WebSocket server
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            logger.debug(f"Received from server: {data}")
                            
                            # Forward message to all overlay clients
                            if self.clients:
                                await asyncio.gather(
                                    *[client.send(message) for client in self.clients],
                                    return_exceptions=True
                                )
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON from server: {message}")
                        except Exception as e:
                            logger.error(f"Error processing server message: {e}")
                            
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Connection to WebSocket server lost: {e}")
                self.ws_client = None
                
                # Wait before reconnecting
                await asyncio.sleep(self.reconnect_delay)
                
            except Exception as e:
                logger.error(f"Unexpected error in WebSocket client: {e}")
                self.ws_client = None
                
                # Wait before reconnecting
                await asyncio.sleep(self.reconnect_delay)
                
    async def send_process_data(self):
        """Periodically send process data to overlay clients from cache"""
        while self.running:
            try:
                # Read process cache
                cache_path = Path('cache/process_sensor/process_cache.json')
                if cache_path.exists():
                    try:
                        with open(cache_path, 'r') as f:
                            data = json.load(f)
                            
                            # Create message
                            message = {
                                "type": "process_update",
                                "data": {
                                    "active_window": data.get("active_window", ""),
                                    "active_app": data.get("active_app", ""),
                                    "timestamp": data.get("timestamp", time.time())
                                }
                            }
                            
                            # Send to clients
                            if self.clients:
                                await asyncio.gather(
                                    *[client.send(json.dumps(message)) for client in self.clients],
                                    return_exceptions=True
                                )
                                logger.debug("Sent process update to clients")
                                
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in process cache")
                    except Exception as e:
                        logger.error(f"Error reading process cache: {e}")
                        
                # Wait before next update
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in process data loop: {e}")
                await asyncio.sleep(5)
                
    def start(self):
        """Start the bridge in a separate thread"""
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                self.running = True
                
                # Create and gather all tasks
                loop.run_until_complete(asyncio.gather(
                    self.start_server(),
                    self.connect_to_ws_server(),
                    self.send_process_data()
                ))
                
            except Exception as e:
                logger.error(f"Error in bridge thread: {e}")
            finally:
                loop.close()
                
        # Start in a daemon thread
        bridge_thread = threading.Thread(target=run_async_loop)
        bridge_thread.daemon = True
        bridge_thread.start()
        
        return bridge_thread
        
    def stop(self):
        """Stop the bridge"""
        self.running = False
        logger.info("Stopping overlay bridge")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    if 'bridge' in globals():
        bridge.stop()
    sys.exit(0)

async def async_main():
    """Async main function"""
    global bridge
    
    # Start the bridge
    bridge = SimpleOverlayBridge()
    bridge_thread = bridge.start()
    logger.info("Started overlay bridge")
    
    # Keep running until terminated
    try:
        while True:
            # Check for input
            await asyncio.sleep(1)
            
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        bridge.stop()
        logger.info("Overlay bridge stopped")

def main():
    """Main function"""
    global bridge
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the bridge
    bridge = SimpleOverlayBridge()
    bridge_thread = bridge.start()
    
    # Print info
    print("\n=== Simplified Overlay Bridge ===")
    print(f"Overlay server running on port 8765")
    print(f"Connecting to WebSocket server on port 8767")
    print("Press Ctrl+C to exit\n")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in main thread: {e}")
    finally:
        bridge.stop()
        logger.info("Overlay bridge stopped")

if __name__ == "__main__":
    main()
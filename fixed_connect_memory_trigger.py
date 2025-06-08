#!/usr/bin/env python3
"""
Fixed Connect Memory Trigger to Chat Overlay

This script bridges the gap between the memory trigger service and the chat overlay
by listening for notification events and forwarding them to the WebSocket server.
The message format has been fixed to match exactly what EnterpriseChatWidget expects.
"""

import asyncio
import json
import logging
import sys
import time
import os
import signal
import websockets
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_trigger_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_trigger_connector")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

class MemoryTriggerConnector:
    """Connects memory trigger service to chat overlay"""
    
    def __init__(self, ws_uri=WS_URI):
        """Initialize connector"""
        self.ws_uri = ws_uri
        self.websocket = None
        self.running = True
        self.last_notification_time = 0
        self.notification_count = 0
        self.memory_system = None
        self.trigger_service = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            # Close existing connection if any
            if self.websocket:
                try:
                    await self.websocket.close()
                except:
                    pass
                
            logger.info(f"Connecting to WebSocket server at {self.ws_uri}")
            
            # Connect with improved parameters
            self.websocket = await websockets.connect(
                self.ws_uri,
                ping_interval=5,
                ping_timeout=20,
                max_size=10 * 1024 * 1024,  # 10MB max message size
                max_queue=32,
                close_timeout=10
            )
            
            logger.info("Connected to WebSocket server")
            
            # Reset reconnect attempts on successful connection
            self.reconnect_attempts = 0
            
            # Receive welcome message with timeout
            try:
                welcome = await asyncio.wait_for(self.websocket.recv(), timeout=10)
                logger.info(f"Received welcome: {welcome[:100]}")
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for welcome message, but connection established")
                
            return True
            
        except Exception as e:
            self.reconnect_attempts += 1
            backoff = min(30, 2 ** self.reconnect_attempts)  # Exponential backoff up to 30 seconds
            logger.error(f"Error connecting to WebSocket server: {e}")
            logger.info(f"Reconnect attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}, next retry in {backoff}s")
            
            # Reset if we've exceeded max attempts
            if self.reconnect_attempts >= self.max_reconnect_attempts:
                self.reconnect_attempts = 0
                
            return False
    
    async def _notification_callback(self, notification):
        """Callback for memory trigger notifications"""
        try:
            # Create direct chat message in the DO button format expected by the server
            direct_message = {
                "type": "do_button",
                "action": "display",
                "content": {
                    "title": notification.title,
                    "message": notification.description or notification.suggestion,
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, help me",
                            "type": "primary"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "type": "secondary"
                        }
                    ]
                },
                "session_id": notification.id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send message to WebSocket
            if self.websocket and not getattr(self.websocket, 'closed', False):
                await self.websocket.send(json.dumps(direct_message))
                logger.info(f"✅ Sent notification to chat overlay: {notification.title}")
                
                self.notification_count += 1
                self.last_notification_time = time.time()
            else:
                logger.warning("WebSocket not connected, attempting to reconnect...")
                connected = await self.connect()
                if connected and self.websocket and not getattr(self.websocket, 'closed', False):
                    await self.websocket.send(json.dumps(direct_message))
                    logger.info(f"✅ Sent notification after reconnection: {notification.title}")
                    
                    self.notification_count += 1
                    self.last_notification_time = time.time()
                else:
                    logger.error("Failed to reconnect, notification not sent")
                
        except Exception as e:
            logger.error(f"Error sending notification to chat overlay: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def start_memory_trigger_service(self):
        """Start memory trigger service with WebSocket integration"""
        try:
            # Import memory components
            from memory.memory_trigger_service import MemoryTriggerService
            from memory.memory_system import MemorySystem
            
            # Create memory system
            self.memory_system = MemorySystem()
            logger.info("Created memory system")
            
            # Create memory trigger service
            self.trigger_service = MemoryTriggerService(memory_system=self.memory_system)
            logger.info("Created memory trigger service")
            
            # Override brain router with our WebSocket connection
            self.trigger_service.brain_router = self
            logger.info("Set brain router to connector")
            
            # Add notification callback using wrapper to properly await the async function
            def notification_callback_wrapper(notification):
                # Create a task to run the async callback
                asyncio.create_task(self._notification_callback(notification))
                
            self.trigger_service.notification_manager.add_notification_callback(notification_callback_wrapper)
            logger.info("Added notification callback with proper async handling")
            
            # Start service
            await self.trigger_service.start()
            logger.info("Started memory trigger service")
            
            return True
        except Exception as e:
            logger.error(f"Error starting memory trigger service: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def process_request(self, request):
        """Mock brain router's process_request method"""
        try:
            # Convert mode to string to make it JSON serializable
            mode_str = "ASK"
            if hasattr(request, 'mode'):
                # Handle if it's an enum or string
                if hasattr(request.mode, '__str__'):
                    mode_str = str(request.mode)
                else:
                    mode_str = request.mode
                    
            # Log the request
            logger.info(f"Processing request: {mode_str} - {request.query}")
            
            # Generate a session ID
            session_id = f"request_{int(datetime.now().timestamp())}"
            if hasattr(request, 'context') and "notification_id" in request.context:
                session_id = request.context["notification_id"]
            
            # For SUGGEST mode requests, use the DO button format
            if mode_str == "SUGGEST" or mode_str == "ChatMode.SUGGEST":
                # Create direct message in the DO button format
                direct_message = {
                    "type": "do_button",
                    "action": "display",
                    "content": {
                        "title": "Suggestion",
                        "message": request.query,
                        "buttons": [
                            {
                                "id": "do_it",
                                "text": "Yes, help me",
                                "type": "primary"
                            },
                            {
                                "id": "dismiss",
                                "text": "No thanks",
                                "type": "secondary"
                            }
                        ]
                    },
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                message_to_send = json.dumps(direct_message)
                logger.info(f"Sending SUGGEST as DO button format")
            else:
                # Convert to chat request message
                message = {
                    "type": "chat_request",
                    "mode": mode_str,
                    "message": request.query,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                }
                
                message_to_send = json.dumps(message)
            
            # Send message to WebSocket with reconnection logic
            # First try with existing connection
            if self.websocket and not getattr(self.websocket, 'closed', False):
                try:
                    await asyncio.wait_for(self.websocket.send(message_to_send), timeout=10)
                    logger.info(f"✅ Successfully sent message to overlay")
                    
                    # Return mock response
                    return type('MockResponse', (), {
                        'success': True,
                        'response': "Message sent to chat overlay"
                    })
                except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                    logger.warning("Connection issue during send, attempting to reconnect...")
            else:
                # Connection issue or not connected, try to reconnect
                logger.warning("WebSocket not connected or connection lost, attempting to reconnect...")
                
            # Try to reconnect
            connected = await self.connect()
            if connected and self.websocket and not getattr(self.websocket, 'closed', False):
                try:
                    await asyncio.wait_for(self.websocket.send(message_to_send), timeout=10)
                    logger.info(f"✅ Successfully sent message after reconnection")
                    
                    # Return mock response
                    return type('MockResponse', (), {
                        'success': True,
                        'response': "Message sent to chat overlay after reconnection"
                    })
                except Exception as e:
                    logger.error(f"Failed to send message after reconnection: {e}")
            
            # If we get here, we couldn't send the message
            logger.error("Failed to send message to overlay after reconnection attempts")
            return type('MockResponse', (), {
                'success': False,
                'response': "Failed to send message to overlay"
            })
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return type('MockResponse', (), {
                'success': False,
                'response': f"Error: {str(e)}"
            })
    
    async def run(self):
        """Run the connector"""
        try:
            # Connect to WebSocket
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect to WebSocket server, exiting")
                return False
            
            # Start memory trigger service
            service_started = await self.start_memory_trigger_service()
            if not service_started:
                logger.error("Failed to start memory trigger service, exiting")
                return False
            
            # Add some test memory items
            await self.add_test_memories()
            
            # Keep running
            while self.running:
                # Print status every minute
                logger.info(f"Memory trigger connector running... Sent {self.notification_count} notifications")
                
                # Reconnect if needed
                if not self.websocket or getattr(self.websocket, 'closed', True):
                    logger.info("Reconnecting to WebSocket server...")
                    await self.connect()
                
                await asyncio.sleep(60)
                
            return True
            
        except Exception as e:
            logger.error(f"Error running connector: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def add_test_memories(self):
        """Add test memories for demonstration"""
        try:
            if not self.memory_system:
                logger.warning("Memory system not available, can't add test memories")
                return False
            
            # Shopping memory
            shopping_memory = {
                "type": "web_content",
                "url": "https://www.amazon.com/products/smartphone",
                "title": "Premium Smartphone XYZ - Amazon.com",
                "searchable_text": """
                Premium Smartphone XYZ with 108MP Camera

                Price: $899.99
                Save $100.00 (10%)
                FREE Shipping
                In Stock.
                
                Buy Now | Add to Cart | Add to List
                
                Features:
                • 6.8" Dynamic AMOLED Display
                • 108MP Camera with 8K Video
                • 5000mAh Battery
                • 5G Connectivity
                
                Product Description:
                Experience the ultimate smartphone with revolutionary camera technology...
                """,
                "timestamp": time.time(),
                "source": "web_browser"
            }
            
            # Form memory
            form_memory = {
                "type": "web_content",
                "url": "https://accounts.google.com/signup",
                "title": "Create your Google Account",
                "searchable_text": """
                Create your Google Account
                
                First name:
                Last name:
                
                Username: @gmail.com
                
                Password:
                Confirm password:
                
                Next | Sign in instead
                
                By creating an account, you agree to our Terms of Service and acknowledge 
                that you have read our Privacy Policy to learn how we collect and use your data.
                """,
                "timestamp": time.time(),
                "source": "web_browser"
            }
            
            # Add memories
            self.memory_system.short_term_memory.append(shopping_memory)
            logger.info("Added shopping memory")
            
            self.memory_system.short_term_memory.append(form_memory)
            logger.info("Added form memory")
            
            return True
        except Exception as e:
            logger.error(f"Error adding test memories: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the connector"""
        self.running = False
        
        # Stop memory trigger service
        if self.trigger_service:
            await self.trigger_service.stop()
            logger.info("Stopped memory trigger service")
        
        # Close WebSocket
        if self.websocket:
            await self.websocket.close()
            logger.info("Closed WebSocket connection")

async def main():
    """Main function"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs/memory', exist_ok=True)
    
    logger.info("🚀 Starting memory trigger connector")
    
    # Create connector
    connector = MemoryTriggerConnector()
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for signame in {'SIGINT', 'SIGTERM'}:
        try:
            loop.add_signal_handler(
                getattr(signal, signame),
                lambda: asyncio.create_task(connector.shutdown())
            )
        except NotImplementedError:
            # Windows does not support add_signal_handler
            pass
    
    # Verify WebSocket server is running on port 8765
    try:
        logger.info("Checking if WebSocket server is running on port 8765...")
        test_websocket = await websockets.connect("ws://localhost:8765")
        await test_websocket.close()
        logger.info("✅ WebSocket server is running on port 8765")
    except Exception as e:
        logger.error(f"❌ WebSocket server is not running on port 8765: {e}")
        logger.error("Please make sure overlay/minimal_ws_server.py is running")
        logger.error("You can start it with: python overlay/minimal_ws_server.py")
        
        # Create a simple guide for the user
        guide_message = """
TROUBLESHOOTING GUIDE:

1. Start WebSocket server on port 8765:
   python overlay/minimal_ws_server.py
   
2. Test direct notification sending:
   python fixed_test_direct_chat_message.py
   
3. Once both tests pass, run this connector again:
   python fixed_connect_memory_trigger.py
"""
        logger.info(guide_message)
        return False
    
    # Run connector
    success = await connector.run()
    
    if success:
        logger.info("✅ Memory trigger connector stopped successfully")
    else:
        logger.error("❌ Memory trigger connector stopped with errors")
        
    return success

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Memory trigger connector stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
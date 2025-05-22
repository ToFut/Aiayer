#!/usr/bin/env python3
"""
LLM Context Connector

This module connects the LLM service to the context memory system, ensuring that:
1. LLM has access to the latest context from memory
2. LLM can provide context-aware responses
3. Context is properly formatted for the LLM's consumption
"""
import json
import os
import time
import logging
import traceback
import asyncio
import websockets
import sys
from datetime import datetime

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/llm_context_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('llm_context_connector')

# Configuration
BRIDGE_WS_URI = "ws://localhost:8766"
LLM_WS_URI = "ws://localhost:8765"  # Changed from 8770 to 8765 to match WebSocket server
MEMORY_STATE_FILE = "memory/memory_state.json"
CONTEXT_FILE = "memory/last_context.json"
CHECK_INTERVAL = 5  # seconds

class LLMContextConnector:
    """
    Connects the LLM service with the context memory system,
    ensuring the LLM has the latest context information.
    """
    
    def __init__(self):
        self.running = True
        self.last_context_update = 0
        self.bridge_websocket = None
        self.llm_websocket = None
        self.context_data = {}
        
        logger.info("LLM Context Connector initialized")
    
    async def read_context_file(self):
        """Read context from memory/last_context.json"""
        try:
            if os.path.exists(CONTEXT_FILE):
                # Check if file was modified since last read
                mod_time = os.path.getmtime(CONTEXT_FILE)
                if mod_time > self.last_context_update:
                    self.last_context_update = mod_time
                    with open(CONTEXT_FILE, 'r') as f:
                        self.context_data = json.load(f)
                    logger.info(f"Read updated context from {CONTEXT_FILE}")
                    return self.context_data
                else:
                    # No changes since last read
                    return self.context_data
            else:
                logger.warning(f"Context file {CONTEXT_FILE} does not exist")
                return {}
        except Exception as e:
            logger.error(f"Error reading context file: {e}")
            logger.error(traceback.format_exc())
            return {}
    
    def format_context_for_llm(self, context):
        """Format context data for LLM consumption"""
        try:
            # Extract relevant fields from context
            active_window = context.get('active_window', '')
            active_app = context.get('active_app', '')
            
            # Get active apps and convert to a simple list if it's a list of objects
            active_apps = context.get('active_apps', [])
            if active_apps and isinstance(active_apps, list) and isinstance(active_apps[0], dict):
                active_apps = [app.get('name', '') for app in active_apps if app.get('name')]
                
            # Get only browser and productivity apps for cleaner context
            browser_apps = [app for app in active_apps if isinstance(app, dict) and app.get('type') == 'browser']
            if not browser_apps:
                browser_apps = [app for app in active_apps if isinstance(app, str) and 'chrome' in app.lower() or 'safari' in app.lower() or 'firefox' in app.lower()]
                
            productivity_apps = [app for app in active_apps if isinstance(app, dict) and app.get('type') == 'productivity']
            if not productivity_apps:
                productivity_apps = [app for app in active_apps if isinstance(app, str) and ('office' in app.lower() or 'word' in app.lower() or 'excel' in app.lower() or 'docs' in app.lower())]
                
            # Extract window history
            window_history = context.get('window_history', [])[:5]  # Only take the 5 most recent
            
            # Get screen text, but limit to a reasonable size
            screen_text = context.get('screen_text', '')
            if screen_text and len(screen_text) > 1000:
                screen_text = screen_text[:1000] + "..."
            
            # Format into a clean, structured context for the LLM
            formatted_context = {
                "user_environment": {
                    "current_window": active_window,
                    "current_application": active_app,
                    "recently_used_windows": window_history,
                    "browser_applications": browser_apps[:5],  # Limit to 5
                    "productivity_applications": productivity_apps[:5]  # Limit to 5
                }
            }
            
            # Only include screen text if it's not empty
            if screen_text:
                formatted_context["screen_content"] = {
                    "text": screen_text
                }
            
            return formatted_context
        except Exception as e:
            logger.error(f"Error formatting context for LLM: {e}")
            logger.error(traceback.format_exc())
            return {"error": "Failed to format context"}
    
    async def connect_to_bridge(self):
        """Connect to bridge server"""
        retry_delay = 5
        while self.running:
            try:
                self.bridge_websocket = await websockets.connect(BRIDGE_WS_URI)
                logger.info(f"Connected to bridge server at {BRIDGE_WS_URI}")
                
                # Register as LLM client
                await self.bridge_websocket.send(json.dumps({
                    "type": "register",
                    "client_type": "llm",
                    "version": "1.0",
                    "capabilities": ["context_aware_responses"],
                    "timestamp": time.time(),
                    "payload": {
                        "client_type": "llm",
                        "sensor_type": "context_provider"
                    }
                }))
                
                # Wait for registration confirmation
                response = await self.bridge_websocket.recv()
                data = json.loads(response)
                if data.get('type') == 'registration_confirmed':
                    logger.info("Registration with bridge server confirmed")
                    
                    # Process messages
                    await self.process_bridge_messages()
                else:
                    logger.warning(f"Unexpected registration response: {data.get('type')}")
                    await asyncio.sleep(retry_delay)
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"Bridge server connection lost: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error in bridge connection: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(retry_delay)
    
    async def connect_to_llm(self):
        """Connect to LLM service"""
        retry_delay = 5
        while self.running:
            try:
                self.llm_websocket = await websockets.connect(LLM_WS_URI)
                logger.info(f"Connected to LLM service at {LLM_WS_URI}")
                
                # Register with LLM
                await self.llm_websocket.send(json.dumps({
                    "type": "register",
                    "client_type": "llm",
                    "version": "1.0",
                    "capabilities": ["context_aware_responses"],
                    "timestamp": time.time(),
                    "payload": {
                        "client_type": "llm",
                        "sensor_type": "context_provider"
                    }
                }))
                
                # Process messages from LLM
                await self.process_llm_messages()
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                logger.warning(f"LLM service connection lost: {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error in LLM connection: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(retry_delay)
    
    async def process_bridge_messages(self):
        """Process messages from bridge server"""
        try:
            async for message in self.bridge_websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    if message_type == 'ping':
                        # Respond to ping
                        await self.bridge_websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": time.time()
                        }))
                    elif message_type == 'user_message':
                        # Forward user message to LLM with context
                        user_message = data.get('message', '')
                        await self.send_context_enriched_message(user_message)
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from bridge")
                except Exception as e:
                    logger.error(f"Error processing bridge message: {e}")
                    logger.error(traceback.format_exc())
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Bridge server connection closed")
    
    async def process_llm_messages(self):
        """Process messages from LLM service"""
        try:
            async for message in self.llm_websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    if message_type == 'ping':
                        # Respond to ping
                        await self.llm_websocket.send(json.dumps({
                            "type": "pong",
                            "timestamp": time.time()
                        }))
                    elif message_type == 'request_context':
                        # LLM is requesting context
                        await self.send_context_to_llm()
                    elif message_type == 'llm_response':
                        # Forward LLM response to bridge
                        if self.bridge_websocket:
                            await self.bridge_websocket.send(message)
                            logger.info("Forwarded LLM response to bridge")
                    
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from LLM")
                except Exception as e:
                    logger.error(f"Error processing LLM message: {e}")
                    logger.error(traceback.format_exc())
        except websockets.exceptions.ConnectionClosed:
            logger.warning("LLM service connection closed")
    
    async def send_context_to_llm(self):
        """Send context to LLM service"""
        try:
            # Read latest context
            context = await self.read_context_file()
            
            # Format for LLM
            formatted_context = self.format_context_for_llm(context)
            
            # Send to LLM
            if self.llm_websocket:
                await self.llm_websocket.send(json.dumps({
                    "type": "context_update",
                    "context": formatted_context,
                    "timestamp": time.time()
                }))
                logger.info("Sent context update to LLM service")
        except Exception as e:
            logger.error(f"Error sending context to LLM: {e}")
            logger.error(traceback.format_exc())
    
    async def send_context_enriched_message(self, message):
        """Send user message to LLM with context"""
        try:
            # Read latest context
            context = await self.read_context_file()
            
            # Format for LLM
            formatted_context = self.format_context_for_llm(context)
            
            # Send to LLM
            if self.llm_websocket:
                await self.llm_websocket.send(json.dumps({
                    "type": "user_message",
                    "message": message,
                    "context": formatted_context,
                    "timestamp": time.time()
                }))
                logger.info("Sent context-enriched user message to LLM service")
        except Exception as e:
            logger.error(f"Error sending context-enriched message to LLM: {e}")
            logger.error(traceback.format_exc())
    
    async def periodic_context_update(self):
        """Periodically check and update context"""
        while self.running:
            try:
                # Read latest context
                context = await self.read_context_file()
                
                # Send to LLM if connected
                if self.llm_websocket and context:
                    formatted_context = self.format_context_for_llm(context)
                    await self.llm_websocket.send(json.dumps({
                        "type": "context_update",
                        "context": formatted_context,
                        "timestamp": time.time()
                    }))
                    logger.info("Sent periodic context update to LLM service")
            except Exception as e:
                logger.error(f"Error in periodic context update: {e}")
                
            await asyncio.sleep(CHECK_INTERVAL)
    
    async def run(self):
        """Run the LLM context connector"""
        try:
            # Save PID
            os.makedirs("pids", exist_ok=True)
            with open('pids/llm_context_connector.pid', 'w') as f:
                f.write(str(os.getpid()))
                
            logger.info("Starting LLM context connector")
            
            # Start tasks
            bridge_task = asyncio.create_task(self.connect_to_bridge())
            llm_task = asyncio.create_task(self.connect_to_llm())
            update_task = asyncio.create_task(self.periodic_context_update())
            
            # Wait for tasks to complete (they run indefinitely)
            await asyncio.gather(bridge_task, llm_task, update_task)
        except Exception as e:
            logger.error(f"Error in main function: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)

async def main():
    """Main function"""
    connector = LLMContextConnector()
    await connector.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("LLM context connector stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
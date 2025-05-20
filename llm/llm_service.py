#!/usr/bin/env python3
"""
LLM Service
Handles LLM operations and WebSocket communication with the bridge server.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.client import WebSocketClientProtocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/aiayer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LLMService:
    """LLM service that handles language model operations and WebSocket communication."""
    
    def __init__(self, server_uri: str = "ws://127.0.0.1:8765"):
        self.server_uri = server_uri
        self.ws: Optional[WebSocketClientProtocol] = None
        self.client_id = str(uuid.uuid4())
        self.running = False
        self.reconnect_delay = 3
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        
        # Initialize LLM client
        self.llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM client."""
        try:
            # Import and initialize your preferred LLM client here
            # For example, using OpenAI:
            # import openai
            # self.llm_client = openai.Client()
            
            # For now, we'll use a mock client
            self.llm_client = MockLLMClient()
            logger.info("LLM client initialized")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
            self.llm_client = None
    
    async def start(self):
        """Start the LLM service."""
        try:
            if not self.llm_client:
                logger.error("LLM client not initialized")
                return False
            
            # Start WebSocket connection
            self.running = True
            await self._connect()
            return True
        except Exception as e:
            logger.error(f"Error starting LLM service: {e}")
            return False
    
    async def stop(self):
        """Stop the LLM service."""
        self.running = False
        if self.ws:
            await self.ws.close()
    
    async def _connect(self):
        """Connect to the WebSocket server."""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to {self.server_uri}")
                async with websockets.connect(self.server_uri) as websocket:
                    self.ws = websocket
                    self.reconnect_attempts = 0
                    
                    # Send connection message
                    await self._send_connection_message()
                    
                    # Handle messages
                    await self._handle_messages()
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting to reconnect...")
            except Exception as e:
                logger.error(f"Connection error: {e}")
            
            if self.running:
                self.reconnect_attempts += 1
                await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
    
    async def _send_connection_message(self):
        """Send initial connection message to server."""
        try:
            await self.ws.send(json.dumps({
                "type": "connection_established",
                "payload": {
                    "client_type": "llm",
                    "client_id": self.client_id,
                    "version": "1.0.0",
                    "capabilities": ["text_generation", "completion"],
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent connection message")
        except Exception as e:
            logger.error(f"Error sending connection message: {e}")
    
    async def _handle_messages(self):
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON message received")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
        except Exception as e:
            logger.error(f"Error in message handler: {e}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message."""
        try:
            msg_type = data.get('type')
            
            if msg_type == 'generate_text':
                # Generate text using LLM
                await self._handle_text_generation(data.get('data', {}))
            elif msg_type == 'complete_text':
                # Complete text using LLM
                await self._handle_text_completion(data.get('data', {}))
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_text_generation(self, data: Dict[str, Any]):
        """Handle text generation request."""
        try:
            prompt = data.get('prompt', '')
            if not prompt:
                raise ValueError("No prompt provided")
            
            # Log the final prompt being sent to the LLM
            logger.info(f"🤖 SENDING PROMPT TO LLM:")
            logger.info(f"  - Prompt: {prompt[:200]}...")
            if len(prompt) > 200:
                logger.info(f"  - Full prompt length: {len(prompt)} chars")
            
            # Log any additional context or parameters
            if 'context' in data:
                logger.info(f"  - Context keys: {list(data['context'].keys())}")
                logger.info(f"  - Context size: {len(str(data['context']))} chars")
            
            # Generate text using LLM
            response = await self.llm_client.generate_text(prompt)
            
            # Log the response
            logger.info(f"✅ LLM RESPONSE RECEIVED:")
            logger.info(f"  - Response length: {len(response)} chars")
            logger.info(f"  - Response preview: {response[:200]}...")
            
            # Send response
            await self.ws.send(json.dumps({
                "type": "llm_response",
                "data": {
                    "text": response,
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent text generation response")
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            await self._send_error("Error generating text", str(e))
    
    async def _handle_text_completion(self, data: Dict[str, Any]):
        """Handle text completion request."""
        try:
            text = data.get('text', '')
            if not text:
                raise ValueError("No text provided")
            
            # Complete text using LLM
            completion = await self.llm_client.complete_text(text)
            
            # Send response
            await self.ws.send(json.dumps({
                "type": "llm_response",
                "data": {
                    "completion": completion,
                    "original_text": text,
                    "timestamp": datetime.now().isoformat()
                }
            }))
            logger.info("Sent text completion response")
        except Exception as e:
            logger.error(f"Error completing text: {e}")
            await self._send_error("Error completing text", str(e))
    
    async def _send_error(self, message: str, details: str = ""):
        """Send error message to server."""
        try:
            await self.ws.send(json.dumps({
                "type": "error",
                "data": {
                    "message": message,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                }
            }))
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

class MockLLMClient:
    """Mock LLM client for testing."""
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text from prompt."""
        return f"Generated response for: {prompt}"
    
    async def complete_text(self, text: str) -> str:
        """Complete text."""
        return f"{text} [completed]"

async def main():
    """Main function to start the LLM service."""
    service = LLMService()
    if await service.start():
        try:
            # Keep the service running
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        finally:
            await service.stop()
    else:
        logger.error("Failed to start service")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1) 
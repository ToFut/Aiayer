#!/usr/bin/env python3
"""
LLM Service
Handles LLM operations and HTTP communication with Ollama API.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import traceback
from contextlib import asynccontextmanager
import time
import websockets
from websockets.exceptions import ConnectionClosed

# Import the prompt logger
from llm.llm_prompt_logger import prompt_logger

# Import the warmup manager for fast responses
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from llm_warmup_manager import get_warmup_manager
    WARMUP_MANAGER_AVAILABLE = True
    logging.getLogger(__name__).info("🔥 LLM Warmup Manager available")
except ImportError:
    WARMUP_MANAGER_AVAILABLE = False
    logging.getLogger(__name__).warning("⚠️ LLM Warmup Manager not available")

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the suggestion detector
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from llm_suggestion_detector import SuggestionDetector
    SUGGESTION_DETECTOR_AVAILABLE = True
except ImportError:
    print("Warning: Suggestion detector not available")
    SUGGESTION_DETECTOR_AVAILABLE = False

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

class SessionManager:
    """Manages aiohttp ClientSession instances to prevent unclosed sessions"""
    def __init__(self):
        self._session = None
        self._lock = asyncio.Lock()
    
    async def get_session(self):
        """Get or create a ClientSession instance"""
        async with self._lock:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=aiohttp.TCPConnector(
                        limit=10,
                        ttl_dns_cache=300,
                        use_dns_cache=True
                    )
                )
            return self._session
    
    async def close(self):
        """Close the current session"""
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

# Create global session manager
session_manager = SessionManager()

@asynccontextmanager
async def get_http_session():
    """Context manager for getting an HTTP session"""
    session = await session_manager.get_session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Error in HTTP session: {e}")
        raise

class LLMService:
    """LLM service that handles language model operations and WebSocket communication."""
    
    def __init__(self, model_name="llama3.2:1b", host="localhost", port=11434, ws_port=8765):
        """
        Initialize the LLM interface.
        
        Args:
            model_name (str): Name of the Ollama model to use
            host (str): Hostname where Ollama API is running
            port (int): Port for Ollama API
            ws_port (int): Port for WebSocket server
        """
        self.model_name = model_name
        self.host = host
        self.port = port
        self.ws_port = ws_port
        self.base_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.clients = set()
        self.last_request_time = 0
        self.min_request_interval = 0.1
        self.timeout = 30
        self.max_retries = 2
        
        # Initialize LLM client
        self.llm_client = None
        self._initialize_llm()
        
        # Initialize WebSocket server
        self.ws_server = None
    
    def _initialize_llm(self):
        """Initialize the LLM client with warmup manager."""
        try:
            # Always create a fallback LocalLLM client
            from llm.model import LocalLLM
            self.llm_client = LocalLLM(model_name=self.model_name)
            
            # Check if warmup manager is available
            if WARMUP_MANAGER_AVAILABLE:
                logger.info("🔥 Initializing with LLM Warmup Manager for fast responses")
                logger.info("📋 Standard LLM client created as fallback")
                # Warmup manager will be initialized async in start()
                self.use_warmup_manager = True
            else:
                logger.info("⚠️ Using standard LLM client only")
                self.use_warmup_manager = False
            
            self.running = True
            logger.info("LLM client initialized")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
            logger.error(f"Python path: {sys.path}")  # Add debug logging
            self.llm_client = None
            self.running = False

    async def initialize(self) -> bool:
        """Initialize the LLM service."""
        try:
            # The LLM client is already initialized in __init__
            if self.llm_client is None:
                self._initialize_llm()
            
            if self.llm_client is not None:
                logger.info(f"LLM service initialized with model: {self.model_name}")
                return True
            else:
                logger.error("Failed to initialize LLM client")
                return False
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False
    
    async def start(self):
        """Start the LLM service and WebSocket server."""
        try:
            # Start WebSocket server
            self.ws_server = await websockets.serve(
                self._handle_websocket,
                "localhost",
                self.ws_port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info(f"WebSocket server started on ws://localhost:{self.ws_port}")
            self.running = True
            
            # Keep the server running
            await self.ws_server.wait_closed()
            
        except Exception as e:
            logger.error(f"Error starting LLM service: {e}")
            return False
    
    async def stop(self):
        """Stop the LLM service and WebSocket server."""
        self.running = False
        if self.ws_server:
            self.ws_server.close()
            await self.ws_server.wait_closed()
        logger.info("LLM service stopped")

    async def cleanup(self):
        """Cleanup resources used by the LLM service."""
        try:
            await self.stop()
            logger.info("LLM service cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up LLM service: {e}")
    
    async def _handle_websocket(self, websocket, path):
        """Handle WebSocket connections."""
        client_id = str(uuid.uuid4())
        self.clients.add(websocket)
        
        try:
            logger.info(f"New client connected: {client_id}")
            
            # Send connection confirmation
            await websocket.send(json.dumps({
                "type": "connection_established",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON message from client {client_id}")
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
                    await self._send_error(websocket, "Error processing message", str(e))
                    
        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client {client_id} removed from active connections")
    
    async def _process_message(self, websocket, data: Dict[str, Any]):
        """Process incoming WebSocket message."""
        try:
            msg_type = data.get('type')
            
            if msg_type == 'text_generation':
                response = await self._handle_text_generation(data)
                await websocket.send(json.dumps(response))
                
            elif msg_type == 'text_completion':
                response = await self._handle_text_completion(data)
                await websocket.send(json.dumps(response))
                
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                await self._send_error(websocket, "Unknown message type", msg_type)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error(websocket, "Error processing message", str(e))
    
    async def _handle_text_generation(self, data: Dict[str, Any]):
        """Handle text generation request."""
        try:
            prompt = data.get('prompt', '')
            if not prompt:
                raise ValueError("No prompt provided")
            
            # Start timing
            start_time = time.time()
            
            # Log the prompt being sent
            logger.info(f"🤖 SENDING PROMPT TO LLM:")
            logger.info(f"  - Prompt: {prompt[:200]}...")
            if len(prompt) > 200:
                logger.info(f"  - Full prompt length: {len(prompt)} chars")
            
            # Set a timeout for the LLM request to prevent hanging
            try:
                # Create an asyncio task with timeout
                generate_task = asyncio.create_task(self.llm_client.generate_text(prompt))
                response = await asyncio.wait_for(generate_task, timeout=20.0)  # 20 second timeout
                
                if response and not response.startswith("Error:") and len(response) > 10:
                    # Valid response received
                    pass
                else:
                    logger.warning(f"LLM returned invalid response: {response}")
                    response = self._get_fallback_response(prompt)
                    
            except asyncio.TimeoutError:
                logger.error("Ollama request timed out - likely processing a large request")
                # Cancel the task to prevent it from continuing in the background
                if not generate_task.done():
                    generate_task.cancel()
                    try:
                        await generate_task
                    except asyncio.CancelledError:
                        pass
                response = self._get_fallback_response(prompt)
                
            except Exception as llm_error:
                logger.error(f"All Ollama attempts failed: {llm_error}. Using fallback response.")
                response = self._get_fallback_response(prompt)
            
            # End timing
            end_time = time.time()
            
            # Log the response
            logger.info(f"✅ LLM RESPONSE RECEIVED:")
            logger.info(f"  - Response length: {len(response)} chars")
            logger.info(f"  - Response preview: {response[:200]}...")
            
            # Log the interaction using the prompt logger
            prompt_logger.log_interaction(
                prompt=prompt,
                response=response,
                model=self.model_name,
                mode=data.get('mode', 'general'),
                context=data.get('context', {}),
                metadata={
                    'request_id': str(uuid.uuid4()),
                    'temperature': data.get('temperature', 0.7),
                    'max_tokens': data.get('max_tokens', 1024)
                },
                start_time=start_time,
                end_time=end_time
            )
            
            return {
                "type": "llm_response",
                "data": {
                    "text": response,
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"Error generating text: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Log the error using the prompt logger
            prompt_logger.log_error(
                error_type="text_generation_error",
                error_message=error_msg,
                context={
                    'prompt_length': len(prompt) if 'prompt' in locals() else 0,
                    'model': self.model_name,
                    'mode': data.get('mode', 'general')
                }
            )
            
            # Return fallback response instead of raising exception
            fallback_response = self._get_fallback_response(prompt)
            return {
                "type": "llm_response",
                "data": {
                    "text": fallback_response,
                    "prompt": prompt,
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Generate a fallback response when LLM fails."""
        # Generate different types of fallback responses based on prompt type
        prompt_lower = prompt.lower()
        
        if "what am i seeing" in prompt_lower or "what's on my screen" in prompt_lower:
            return "I'm having trouble analyzing your screen right now. Please try again in a moment or describe what you're looking at."
            
        elif "how do i" in prompt_lower or "how to" in prompt_lower:
            return "I'm having trouble processing your how-to question right now. Could you try rephrasing it or asking again in a moment?"
            
        elif "?" in prompt:
            return "I apologize, but I'm experiencing a temporary issue accessing my knowledge. Please try your question again in a moment."
            
        else:
            return "I apologize, but I encountered a temporary issue while processing your request. Please try again in a moment."
    
    async def _handle_text_completion(self, data: Dict[str, Any]):
        """Handle text completion request."""
        try:
            text = data.get('text', '')
            if not text:
                raise ValueError("No text provided")
            
            # Complete text using LLM
            completion = await self.llm_client.complete_text(text)
            
            return {
                "type": "llm_response",
                "data": {
                    "completion": completion,
                    "original_text": text,
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error completing text: {e}")
            return {
                "type": "error",
                "payload": {
                    "message": "Error completing text",
                    "details": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _send_error(self, websocket, message: str, details: str = ""):
        """Send error message to the client."""
        try:
            error_data = {
                "type": "error",
                "payload": {
                    "message": message,
                    "details": details,
                    "timestamp": datetime.now().isoformat()
                }
            }
            await websocket.send(json.dumps(error_data))
            logger.error(f"Error: {message} - {details}")
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

async def main():
    """Main function to run the LLM service."""
    try:
        # Initialize and start the LLM service
        llm_service = LLMService()
        await llm_service.start()
        
    except KeyboardInterrupt:
        logger.info("LLM service stopped by user")
    except Exception as e:
        logger.error(f"Error in LLM service: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Clean up resources
        if 'llm_service' in locals():
            await llm_service.stop()

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 
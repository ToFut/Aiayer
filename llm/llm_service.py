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

class LLMService:
    """LLM service that handles language model operations and WebSocket communication."""
    
    def __init__(self, model_name="llama3.2:latest", host="localhost", port=11434):
        """
        Initialize the LLM interface.
        
        Args:
            model_name (str): Name of the Ollama model to use (llama3.2:latest for chat, llava for screen sensor)
            host (str): Hostname where Ollama API is running
            port (int): Port for Ollama API
        """
        self.model_name = model_name
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Reduced from 1 to 0.5 seconds
        self.timeout = 30  # Reduced from 60 to 30 seconds
        self.max_retries = 2  # Reduced from 3 to 2
        
        # Initialize aiohttp session with connection pooling
        self.session = None
        self._init_session()
        
        # Configure model-specific settings
        if model_name == "llava":
            self.is_vision_model = True
            self.temperature = 0.7
            self.max_tokens = 1024
        else:  # llama3.2:latest
            self.is_vision_model = False
            self.temperature = 0.8
            self.max_tokens = 2048
        
        self.client_id = str(uuid.uuid4())
        self.reconnect_delay = 3
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Initialize LLM client
        self.llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM client."""
        try:
            # Import and initialize Ollama client
            from llm.model import LocalLLM
            self.llm_client = LocalLLM(model_name=self.model_name)  # Use the available model
            # Start the LLM client
            asyncio.create_task(self.llm_client.start())
            self.running = True
            logger.info("LLM client initialized with Ollama")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
            logger.error(f"Python path: {sys.path}")  # Add debug logging
            self.llm_client = None
            self.running = False
    
    async def start(self):
        """Start the LLM service."""
        try:
            if not self.llm_client:
                logger.error("LLM client not initialized")
                return False
            
            # Start HTTP connection
            self.running = True
            await self._connect()
            return True
        except Exception as e:
            logger.error(f"Error starting LLM service: {e}")
            return False
    
    async def stop(self):
        """Stop the LLM service."""
        self.running = False
        if self.session:
            await self.session.close()
    
    async def _connect(self):
        """Connect to the Ollama API."""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                logger.info(f"Connecting to {self.base_url}")
                # Test connection with a simple HTTP request
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/api/tags") as response:
                        if response.status == 200:
                            self.reconnect_attempts = 0
                            logger.info("Successfully connected to Ollama API")
                            # Keep the connection alive
                            while self.running:
                                await asyncio.sleep(30)  # Check connection every 30 seconds
                                try:
                                    async with session.get(f"{self.base_url}/api/tags") as check_response:
                                        if check_response.status != 200:
                                            raise ConnectionError("Ollama API not responding")
                                except Exception as e:
                                    logger.error(f"Connection check failed: {e}")
                                    break
                        else:
                            raise ConnectionError(f"Ollama API returned status {response.status}")
                    
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
            
            if msg_type == 'llm_request':
                # Extract query and context
                payload = data.get('payload', {})
                query = payload.get('query', '')
                context = payload.get('context', {})
                
                # Log context details
                logger.info(f"Processing LLM request with context:")
                if context:
                    logger.info(f"Context keys: {list(context.keys())}")
                    if 'screen' in context:
                        logger.info(f"Screen data: {context['screen'].get('active_app', 'unknown')}")
                    if 'processes' in context:
                        logger.info(f"Process count: {len(context['processes'])}")
                
                # Generate response
                response = await self.generate_response(query, context)
                
                # Log response
                logger.info(f"Generated response: {response[:100]}...")
                
            elif msg_type == 'sensor_data':
                # Update context data from sensors
                self.context_data = data.get('payload', {})
                logger.debug("Context data updated")
                
            elif msg_type == 'ping':
                # Handle ping - send pong
                await self.ws.send(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error("Error processing message", str(e))
            
    async def generate_response(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate a response using the LLM with context."""
        try:
            # Build system message with context
            system_message = "You are a helpful assistant with access to the user's environment context.\n\n"
            
            # Try to load context from last_context.json if not provided
            if not context:
                try:
                    context_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'memory', 'last_context.json')
                    if os.path.exists(context_file):
                        with open(context_file, 'r') as f:
                            loaded_context = json.load(f)
                            if loaded_context:
                                context = loaded_context
                                logger.info(f"Loaded context from {context_file}")
                except Exception as e:
                    logger.warning(f"Could not load context from file: {e}")
            
            # Enhanced context integration
            if context:
                # Add active window and application context
                active_window = context.get('active_window')
                active_app = context.get('active_app')
                if active_window:
                    system_message += f"Active Window: {active_window}\n"
                if active_app:
                    system_message += f"Active Application: {active_app}\n"
                
                # Add running applications
                active_apps = context.get('active_apps', [])
                if active_apps:
                    system_message += "Running Applications:\n"
                    for app in active_apps[:5]:  # Show top 5 apps
                        system_message += f"- {app}\n"
                
                # Add screen content
                screen_text = context.get('screen_text', '')
                if screen_text:
                    # Truncate very long text
                    if len(screen_text) > 1000:
                        truncated_text = screen_text[:1000] + "...(truncated)"
                    else:
                        truncated_text = screen_text
                    system_message += f"\nScreen Content:\n{truncated_text}\n"
                
                # Add window history if available
                window_history = context.get('window_history', [])
                if window_history:
                    system_message += "\nRecent Window History:\n"
                    for window in window_history[:3]:  # Show last 3 windows
                        system_message += f"- {window}\n"
                
                # Add LLaVA visual description if available
                visual_context = context.get('visual_context', '')
                if visual_context:
                    system_message += f"\nVisual Content Description:\n{visual_context}\n"
                    
                # Add timestamp information
                ts = context.get('timestamp')
                if ts:
                    from datetime import datetime
                    date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    system_message += f"\nContext Timestamp: {date_str}\n"
                
            # Add instructions for special queries
            if "what am i seeing" in query.lower() or "what's on my screen" in query.lower():
                system_message += "\nThe user is asking about what they're seeing on their screen. " 
                system_message += "Provide a detailed and helpful summary of their screen content and visual context.\n"
            
            logger.info(f"Generated system message with context: {len(system_message)} chars")
            
            # Prepare messages for LLM
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ]
            
            # Generate response
            response = await self.llm_client.generate_response(messages)
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request."
    
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
            
            # Check if response is a suggestion
            response_type = "llm_response"
            response_data = {
                "text": response,
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use suggestion detector if available
            if SUGGESTION_DETECTOR_AVAILABLE:
                detector = SuggestionDetector()
                is_suggestion, confidence, suggestion_data = detector.detect_suggestion(response)
                
                if is_suggestion:
                    logger.info(f"Detected suggestion with confidence {confidence:.2f}")
                    response_type = "suggestion"
                    response_data = {
                        "content": response,
                        "title": suggestion_data.get('title', 'Suggestion'),
                        "confidence": confidence,
                        "isSuggestion": True,
                        "buttons": suggestion_data.get('buttons', [
                            {'id': 'do', 'label': 'Yes', 'primary': True},
                            {'id': 'adjust', 'label': 'Adjust', 'primary': False},
                            {'id': 'dismiss', 'label': 'No', 'primary': False}
                        ])
                    }
            
            # Send response
            await self.ws.send(json.dumps({
                "type": response_type,
                "data": response_data
            }))
            logger.info(f"Sent {response_type}")
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
            logger.error(f"Error: {message} - {details}")
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
    def _init_session(self):
        """Initialize aiohttp session with connection pooling"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                connector=aiohttp.TCPConnector(
                    limit=10,  # Max concurrent connections
                    ttl_dns_cache=300,  # DNS cache TTL
                    use_dns_cache=True
                )
            )

    async def initialize(self):
        """Initialize the LLM service."""
        try:
            # Initialize the LLM client
            self._initialize_llm()
            
            # Initialize the HTTP session
            self._init_session()
            
            # Test connection to Ollama
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status != 200:
                    raise ConnectionError(f"Failed to connect to Ollama API: {response.status}")
            
            logger.info("LLM service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            return False

    async def cleanup(self):
        """Clean up resources used by the LLM service."""
        try:
            # Close the HTTP session
            if self.session:
                await self.session.close()
                self.session = None
            
            # Stop the LLM client if it exists
            if self.llm_client:
                await self.llm_client.stop()
                self.llm_client = None
            
            logger.info("LLM service cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up LLM service: {e}")

class MockLLMClient:
    """Mock LLM client for testing."""
    
    async def generate_text(self, prompt: str) -> str:
        """Generate text from prompt."""
        return f"Generated response for: {prompt}"
    
    async def complete_text(self, text: str) -> str:
        """Complete text."""
        return f"{text} [completed]"

async def main():
    """Main function to run the LLM service."""
    try:
        # Initialize and start the LLM service
        llm_service = LLMService()
        success = await llm_service.start()
        
        if success:
            logger.info("LLM service started successfully")
            
            # Keep the service running
            while llm_service.running:
                await asyncio.sleep(1)
                
        else:
            logger.error("Failed to start LLM service")
            
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
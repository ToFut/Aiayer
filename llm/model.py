#!/usr/bin/env python3
"""
Local LLM Integration Module
Provides interface to local language models via Ollama.
"""
import os
import json
import logging
import aiohttp
import asyncio
import base64
import time
import traceback
from collections import deque
from typing import List, Dict, Union, Any, Optional
from PIL import Image
import io
from contextlib import asynccontextmanager

import requests

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

class LocalLLM:
    """
    Interface to a locally running language model via Ollama.
    Provides methods to ensure model availability and generate responses.
    
    This class implements both async context manager support and graceful cleanup
    to handle client sessions properly.
    """
    
    def __init__(self, model_name="llama3.2:1b", host="localhost", port=11434):
        """
        Initialize the LLM interface.
        
        Args:
            model_name (str): Name of the Ollama model to use (llama3.2:1b for chat, llava for screen sensor)
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
        self.min_request_interval = 0.1  # 0.1 second between requests for faster throughput
        self.timeout = 120  # Increased timeout for LLM requests (was 60)
        self.streaming_timeout = 300  # Special timeout for streaming requests (5 minutes)
        self.max_retries = 3  # Maximum number of retries
        
        # Configure model-specific settings
        if model_name == "llava":
            self.is_vision_model = True
            self.temperature = 0.7
            self.max_tokens = 1024
        else:  # llama3.2:1b
            self.is_vision_model = False
            self.temperature = 0.8
            self.max_tokens = 2048
    
    # Async context manager support
    async def __aenter__(self):
        """Async context manager entry - initialize the LLM"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - clean up resources"""
        await self.stop()
        # Also close any sessions from session_manager
        await session_manager.close()
        return False  # Don't suppress exceptions
    
    async def start(self):
        """Start the LLM service and verify it's working"""
        try:
            session = await session_manager.get_session()
            async with session.get(
                f"{self.base_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to connect to Ollama API: {response.status}")
                
                data = await response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                if self.model_name not in models:
                    raise Exception(f"Model {self.model_name} not found in available models: {models}")
                
                self.running = True
                self.logger.info(f"✅ LLM service started successfully with model {self.model_name}")
                return True
        except Exception as e:
            self.logger.error(f"❌ Failed to start LLM service: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the LLM service"""
        self.running = False
        self.logger.info("LLM service stopped")
    
    def _encode_image(self, image: Union[Image.Image, bytes, str]) -> str:
        """
        Encode image for LLaVA API.
        
        Args:
            image: PIL Image, bytes, or file path
            
        Returns:
            str: Base64 encoded image
        """
        if isinstance(image, str):
            with open(image, 'rb') as f:
                image_bytes = f.read()
        elif isinstance(image, Image.Image):
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            image_bytes = buffered.getvalue()
        elif isinstance(image, bytes):
            image_bytes = image
        else:
            raise ValueError("Unsupported image type")
            
        return base64.b64encode(image_bytes).decode('utf-8')
    
    async def generate_response(self, messages, stream=False, temperature=0.7, max_tokens=None):
        """
        Generate a response using Ollama API.
        
        Args:
            messages: List of message objects (each with role and content)
            stream: Whether to stream the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        if not self.running:
            self.logger.info("LLM not running, starting it now")
            try:
                await self.start()
            except Exception as e:
                self.logger.error(f"Failed to start LLM: {e}")
                return "Error: LLM service not available"
        
        # Rate limit requests but use faster interval for llama3.2:1b
        if self.model_name == "llama3.2:1b":
            self.min_request_interval = 0.05  # Faster interval for small model
        
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - (current_time - self.last_request_time))
        self.last_request_time = time.time()
        
        # Optimize messages to reduce unnecessary context for small models
        if self.model_name == "llama3.2:1b" and len(messages) > 1:
            # Keep system message but limit its size
            if messages[0]["role"] == "system" and len(messages[0]["content"]) > 500:
                # Truncate very long system messages for faster processing
                messages[0]["content"] = messages[0]["content"][:500] + "..."
            
            # Limit number of context messages to 3 most recent for faster processing
            if len(messages) > 4:
                messages = [messages[0]] + messages[-3:]  # Keep system + 3 most recent
        
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
            
        # For 1b model, use slightly smaller max_tokens if not specified
        elif self.model_name == "llama3.2:1b" and max_tokens is None:
            request_data["max_tokens"] = 512  # Smaller context for faster responses
        
        start_time = time.time()
        
        # Implement retry logic
        for attempt in range(self.max_retries):
            try:
                session = await session_manager.get_session()
                try:
                    self.logger.info(f"Sending Ollama request (attempt {attempt+1}/{self.max_retries})")
                    
                    # Set larger timeout for first attempt
                    if attempt == 0:
                        timeout = self.timeout * 1.5
                    else:
                        timeout = self.timeout
                        
                    # Use stream parameter for all requests to simplify handling
                    request_data["stream"] = True
                    
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        # Check for HTTP errors
                        if response.status != 200:
                            error_msg = f"HTTP error {response.status} on attempt {attempt+1}/{self.max_retries}"
                            
                            if attempt < self.max_retries - 1:
                                self.logger.warning(f"Request failed: {error_msg}, retrying...")
                                await asyncio.sleep(1)  # Wait before retry
                                continue
                            else:
                                self.logger.error(error_msg)
                                return f"Error: Failed to generate response (status {response.status})"
                        
                        # Always read as text, never as JSON - Ollama 0.6.8+ uses NDJSON format
                        try:
                            text = await response.text()
                            self.logger.info(f"Ollama response time: {time.time() - start_time:.2f}s (status: {response.status})")
                            
                            if not text.strip():
                                self.logger.error("Empty response from Ollama")
                                if attempt < self.max_retries - 1:
                                    continue
                                return "Error: Received empty response from Ollama"
                                
                            # Process NDJSON format - always assume streaming
                            full_response = ""
                            lines = [line for line in text.split('\n') if line.strip()]
                            
                            if not lines:
                                self.logger.error("No valid lines in Ollama response")
                                if attempt < self.max_retries - 1:
                                    continue
                                return "Error: Received invalid response from Ollama"
                            
                            # Process each line of the NDJSON stream
                            valid_lines_count = 0
                            for line in lines:
                                try:
                                    data = json.loads(line)
                                    if 'message' in data and 'content' in data['message']:
                                        full_response += data['message']['content']
                                        valid_lines_count += 1
                                    elif 'response' in data:  # Older Ollama format
                                        full_response += data['response']
                                        valid_lines_count += 1
                                except json.JSONDecodeError:
                                    # Skip invalid JSON
                                    continue
                            
                            # Check if we got a valid response
                            if valid_lines_count > 0:
                                self.logger.info(f"Successfully parsed NDJSON response: {len(full_response)} chars from {valid_lines_count} parts")
                                return full_response
                            else:
                                # Try a fallback approach - parse the last line
                                self.logger.warning("No valid message content found in NDJSON response, trying fallback parsing")
                                try:
                                    # Try to extract any text that looks reasonable
                                    import re
                                    text_parts = re.findall(r'"content":"([^"]+)"', text)
                                    if text_parts:
                                        combined = "".join(text_parts)
                                        self.logger.info(f"Extracted content using regex: {len(combined)} chars")
                                        return combined
                                    
                                    # Last resort - just return the text
                                    self.logger.warning("Fallback to returning raw text")
                                    # Remove JSON formatting and just get readable text
                                    cleaned_text = re.sub(r'[{}\[\]"\\]', '', text)
                                    cleaned_text = re.sub(r'response:|content:', ' ', cleaned_text)
                                    return cleaned_text
                                except Exception as fallback_error:
                                    self.logger.error(f"Fallback parsing failed: {fallback_error}")
                                    if attempt < self.max_retries - 1:
                                        continue
                                    return "Error: Failed to parse Ollama response"
                            
                        except asyncio.TimeoutError:
                            self.logger.error(f"Ollama request timed out after {timeout}s")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(0.5 * (attempt + 1))
                                continue
                            return "Error: Request timed out. The model is taking too long to respond."
                            
                        except Exception as e:
                            self.logger.error(f"Unexpected error processing response: {str(e)}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(0.5 * (attempt + 1))
                                continue
                            return f"Error: {str(e)}"
                
                except asyncio.TimeoutError:
                    self.logger.error(f"Ollama request timed out after {timeout}s")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    return "Error: Request timed out. The model is taking too long to respond."
            
            except asyncio.TimeoutError:
                error_msg = f"Request timed out after {self.timeout}s"
                last_error = error_msg
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"{error_msg} after all retries")
                    return "Error: The model is taking too long to respond. Please try a simpler query."
                            
            except aiohttp.ClientConnectorError as e:
                error_msg = f"Connection error: {str(e)}"
                last_error = error_msg
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"{error_msg} after all retries")
                    return "Error: Unable to connect to LLM service. Please check if Ollama is running."
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                last_error = error_msg
                self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    return f"Error: An unexpected problem occurred while generating a response."
        
        self.logger.error(f"Failed to generate response after {self.max_retries} retries. Last error: {last_error}")
        return "Error: Failed to generate response after multiple attempts. The LLM service may be overloaded."
    
    async def generate_response_stream(self, messages, temperature=0.7, max_tokens=None):
        """
        Generate a streaming response using Ollama API.
        
        Args:
            messages: List of message objects (each with role and content)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Generated text chunks
        """
        if not self.running:
            self.logger.info("LLM not running, starting it now")
            try:
                await self.start()
            except Exception as e:
                self.logger.error(f"Failed to start LLM: {e}")
                yield "Error: LLM service not available"
                return
        
        # Rate limit requests
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - (current_time - self.last_request_time))
        self.last_request_time = time.time()
        
        # Optimize messages for small models
        if self.model_name == "llama3.2:1b" and len(messages) > 1:
            if messages[0]["role"] == "system" and len(messages[0]["content"]) > 500:
                messages[0]["content"] = messages[0]["content"][:500] + "..."
            if len(messages) > 4:
                messages = [messages[0]] + messages[-3:]
        
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
        elif self.model_name == "llama3.2:1b" and max_tokens is None:
            request_data["max_tokens"] = 1024  # Increased for complex responses
        
        start_time = time.time()
        chunk_count = 0
        
        # Implement retry logic for streaming
        for attempt in range(self.max_retries):
            try:
                session = await session_manager.get_session()
                try:
                    self.logger.info(f"Sending streaming Ollama request (attempt {attempt+1}/{self.max_retries})")
                    
                    # Use longer timeout for streaming, especially for complex tasks
                    timeout = self.streaming_timeout if attempt == 0 else self.timeout
                    
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        if response.status != 200:
                            error_msg = f"HTTP error {response.status} on attempt {attempt+1}/{self.max_retries}"
                            if attempt < self.max_retries - 1:
                                self.logger.warning(f"Streaming request failed: {error_msg}, retrying...")
                                await asyncio.sleep(1)
                                continue
                            else:
                                self.logger.error(error_msg)
                                yield f"Error: Failed to generate response (status {response.status})"
                                return
                        
                        # Process streaming response with better error handling
                        try:
                            last_chunk_time = time.time()
                            async for line in response.content:
                                current_time = time.time()
                                
                                # Check for timeout during streaming
                                if current_time - last_chunk_time > 30:  # 30s between chunks
                                    self.logger.warning("No chunks received for 30s, continuing...")
                                
                                line_str = line.decode('utf-8').strip()
                                if not line_str:
                                    continue
                                
                                try:
                                    data = json.loads(line_str)
                                    # Extract content from the message field
                                    if 'message' in data and 'content' in data['message']:
                                        content = data['message']['content']
                                        if content:
                                            chunk_count += 1
                                            last_chunk_time = current_time
                                            yield content
                                    elif 'response' in data:
                                        content = data['response']
                                        if content:
                                            chunk_count += 1
                                            last_chunk_time = current_time
                                            yield content
                                    elif 'done' in data and data['done']:
                                        # Stream completed successfully
                                        break
                                except json.JSONDecodeError:
                                    continue
                            
                            elapsed = time.time() - start_time
                            self.logger.info(f"Streaming completed: {chunk_count} chunks in {elapsed:.2f}s")
                            return
                            
                        except asyncio.TimeoutError:
                            self.logger.error(f"Streaming request timed out after {timeout}s")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(0.5 * (attempt + 1))
                                continue
                            yield "Error: Request timed out. The model is taking too long to respond."
                            return
                            
                        except Exception as e:
                            self.logger.error(f"Unexpected error processing streaming response: {str(e)}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(0.5 * (attempt + 1))
                                continue
                            yield f"Error: {str(e)}"
                            return
                
                except asyncio.TimeoutError:
                    self.logger.error(f"Streaming request timed out after {timeout}s")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))
                        continue
                    yield "Error: Request timed out. The model is taking too long to respond."
                    return
            
            except asyncio.TimeoutError:
                error_msg = f"Streaming request timed out after {self.streaming_timeout}s"
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"{error_msg} after all retries")
                    yield "Error: The model is taking too long to respond. Please try a simpler query."
                    return
                        
            except aiohttp.ClientConnectorError as e:
                error_msg = f"Connection error: {str(e)}"
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"{error_msg} after all retries")
                    yield "Error: Unable to connect to LLM service. Please check if Ollama is running."
                    return
                    
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    yield f"Error: An unexpected problem occurred while generating a response."
                    return
        
        self.logger.error(f"Failed to generate streaming response after {self.max_retries} retries")
        yield "Error: Failed to generate response after multiple attempts. The LLM service may be overloaded."

# Create OllamaLLM as an alias for compatibility
OllamaLLM = LocalLLM

# For testing if run directly
if __name__ == "__main__":
    asyncio.run(main())
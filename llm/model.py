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
from typing import List, Dict, Union
from PIL import Image
import io

import requests

class LocalLLM:
    """
    Interface to a locally running language model via Ollama.
    Provides methods to ensure model availability and generate responses.
    """
    
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
        self.min_request_interval = 0.1  # 0.1 second between requests for faster throughput
        self.timeout = 20  # Balanced timeout for fast models like llama3.2:1b
        self.max_retries = 3  # Maximum number of retries
        
        # Configure model-specific settings
        if model_name == "llava":
            self.is_vision_model = True
            self.temperature = 0.7
            self.max_tokens = 1024
        else:  # llama3.2:latest
            self.is_vision_model = False
            self.temperature = 0.8
            self.max_tokens = 2048
    
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
    
    async def generate_response_with_image(self, messages: List[Dict[str, str]], image: Union[Image.Image, bytes, str]) -> str:
        """
        Generate a response from the model with image input.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            image: PIL Image, bytes, or file path to the image
            
        Returns:
            str: Generated response text
        """
        if not self.running:
            self.logger.error("LLM not running")
            await self.start()  # Attempt to start the LLM automatically
            if not self.running:
                return "Error: LLM service unavailable. Please check if Ollama is running."
            
        if not messages:
            self.logger.error("Empty messages list")
            return "Error: Empty messages list"
            
        # Encode image with detailed error handling
        try:
            image_base64 = self._encode_image(image)
        except FileNotFoundError as e:
            self.logger.error(f"Image file not found: {e}")
            return "Error: The image file could not be found. Please verify the file path."
        except PermissionError as e:
            self.logger.error(f"Permission error accessing image: {e}")
            return "Error: Permission denied when trying to access the image file."
        except ValueError as e:
            self.logger.error(f"Invalid image format: {e}")
            return "Error: The provided image is in an unsupported format."
        except Exception as e:
            self.logger.error(f"Error encoding image: {e}\n{traceback.format_exc()}")
            return "Error: Failed to process the image for analysis."
            
        # Prepare request with image and optimized LLaVA prompt
        prompt_messages = messages.copy()
        
        # Enhance system prompt for better image analysis if it exists
        system_prompt_added = False
        for i, msg in enumerate(prompt_messages):
            if msg['role'] == 'system':
                msg['content'] = f"""You are a visual analysis assistant powered by LLaVA, specialized in analyzing screen content.
When analyzing images:
1. First describe what you see in the image in detail
2. Identify key UI elements such as buttons, text fields, and menus
3. Recognize any text content visible in the image
4. Understand the context of what the user is working on
5. Provide relevant, helpful responses based on the visual context

{msg['content']}"""
                system_prompt_added = True
                break
        
        # Add system prompt if none exists
        if not system_prompt_added:
            prompt_messages.insert(0, {
                'role': 'system',
                'content': """You are a visual analysis assistant powered by LLaVA, specialized in analyzing screen content.
When analyzing images:
1. First describe what you see in the image in detail
2. Identify key UI elements such as buttons, text fields, and menus
3. Recognize any text content visible in the image
4. Understand the context of what the user is working on
5. Provide relevant, helpful responses based on the visual context"""
            })
        
        # Prepare the request with enhanced prompting
        request_data = {
            "model": self.model_name,
            "messages": prompt_messages,
            "images": [image_base64],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        # Retry logic with improved error handling
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Use optimized timeout settings for image requests
                # Images take longer to process, so use longer timeout
                timeout = aiohttp.ClientTimeout(
                    connect=5,       # Connect timeout: 5 seconds
                    total=self.timeout * 1.5  # 50% longer timeout for image processing
                )
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    try:
                        # Log attempt for debugging
                        if attempt > 0:
                            self.logger.info(f"Retry attempt {attempt+1}/{self.max_retries} for image request")
                            
                        start_time = time.time()
                        response = await session.post(
                            f"{self.base_url}/api/chat",
                            json=request_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        # Log response time for performance monitoring
                        elapsed = time.time() - start_time
                        self.logger.info(f"Ollama image response time: {elapsed:.2f}s (status: {response.status})")
                        
                        if response.status != 200:
                            error_msg = f"Error generating image response: HTTP {response.status}"
                            if attempt < self.max_retries - 1:
                                self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                                await asyncio.sleep(1.0 * (attempt + 1))  # Longer backoff for image processing
                                continue
                            else:
                                self.logger.error(error_msg)
                                return f"Error: Failed to analyze image (status {response.status})"
                        
                        # Parse response with detailed error handling
                        try:
                            data = await response.json()
                            if isinstance(data, dict) and 'message' in data:
                                result = data['message']['content']
                                # Log success for monitoring
                                self.logger.info(f"Successfully generated image response ({len(result)} chars)")
                                return result
                            else:
                                self.logger.error(f"Invalid image response format: {data}")
                                return "Error: Received unexpected response format from image analysis"
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse JSON response for image: {e}")
                            return "Error: Received invalid response from image analysis service"
                            
                    except asyncio.TimeoutError:
                        error_msg = f"Image request timed out after {self.timeout * 1.5}s"
                        last_error = error_msg
                        if attempt < self.max_retries - 1:
                            self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                            await asyncio.sleep(1.0 * (attempt + 1))
                            continue
                        else:
                            self.logger.error(f"{error_msg} after all retries")
                            return "Error: The image analysis is taking too long. The image may be too complex or the system is overloaded."
                            
            except aiohttp.ClientConnectorError as e:
                error_msg = f"Connection error during image analysis: {str(e)}"
                last_error = error_msg
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                else:
                    self.logger.error(f"{error_msg} after all retries")
                    return "Error: Unable to connect to image analysis service. Please check if Ollama is running."
                    
            except Exception as e:
                error_msg = f"Unexpected error during image analysis: {str(e)}"
                last_error = error_msg
                self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                else:
                    return f"Error: An unexpected problem occurred during image analysis."
        
        self.logger.error(f"Failed to analyze image after {self.max_retries} retries. Last error: {last_error}")
        return "Error: Failed to analyze the image after multiple attempts. The service may be overloaded or the image may be too complex."
    
    async def initialize(self):
        """
        Asynchronously initialize the LLM by checking Ollama version and model availability.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Check Ollama version
                response = await session.get(f"{self.base_url}/api/version", timeout=2)
                if response.status != 200:
                    raise ConnectionError("Failed to connect to Ollama")
                
                # Check if model is available
                response = await session.get(f"{self.base_url}/api/tags", timeout=2)
                if response.status != 200:
                    raise ConnectionError("Failed to get model list")
                
                # Get models list
                response_data = await response.json()
                models = [model['name'] for model in response_data.get('models', [])]
                
                if self.model_name not in models:
                    self.logger.info(f"Model {self.model_name} not found, pulling...")
                    response = await session.post(
                        f"{self.base_url}/api/pull",
                        json={"name": self.model_name},
                        timeout=30  # Longer timeout for pull
                    )
                    if response.status != 200:
                        raise ConnectionError("Failed to pull model")
                    
                    # Wait for model to be pulled
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if 'error' in data:
                                raise ConnectionError(f"Error pulling model: {data['error']}")
            
            self.running = True
            return self
            
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")
            self.running = False
            raise
    
    async def ensure_model_available(self):
        """
        Ensure the model is available locally.
        Returns True if model is available or successfully pulled, False otherwise.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                response = await session.get(f"{self.base_url}/api/version", timeout=5)
                if response.status != 200:
                    self.logger.error("Failed to connect to Ollama")
                    return False
                
                # Check if model is available
                response = await session.get(f"{self.base_url}/api/tags")
                if response.status != 200:
                    self.logger.error("Failed to get model list")
                    return False
                
                response_data = await response.json()
                models = [model['name'] for model in response_data.get('models', [])]
                
                if self.model_name not in models:
                    self.logger.info(f"Model {self.model_name} not found, pulling...")
                    response = await session.post(
                        f"{self.base_url}/api/pull",
                        json={"name": self.model_name},
                        timeout=30  # Longer timeout for pull
                    )
                    if response.status != 200:
                        self.logger.error("Failed to pull model")
                        return False
                    
                    # Wait for model to be pulled
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if 'error' in data:
                                self.logger.error(f"Error pulling model: {data['error']}")
                                return False
                
                self.running = True
                return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring model availability: {e}")
            return False
    
    async def start(self):
        """Start the LLM model."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                response = await session.get(f"{self.base_url}/api/version", timeout=5)
                if response.status != 200:
                    self.logger.error("Failed to connect to Ollama")
                    return False
                version_data = await response.json()
                self.logger.info(f"Connected to Ollama version: {version_data.get('version')}")
                
                # Check if model is available
                response = await session.get(f"{self.base_url}/api/tags")
                if response.status != 200:
                    self.logger.error("Failed to get model list")
                    return False
                
                response_data = await response.json()
                models = [model['name'] for model in response_data.get('models', [])]
                
                if self.model_name not in models:
                    self.logger.info(f"Model {self.model_name} not found, pulling...")
                    response = await session.post(
                        f"{self.base_url}/api/pull",
                        json={"name": self.model_name},
                        timeout=30  # Longer timeout for pull
                    )
                    if response.status != 200:
                        self.logger.error("Failed to pull model")
                        return False
                    
                    # Wait for model to be pulled
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if 'error' in data:
                                self.logger.error(f"Error pulling model: {data['error']}")
                                return False
                
                self.running = True
                return True
                
        except Exception as e:
            self.logger.error(f"Error starting LLM: {e}")
            return False
    
    async def stop(self):
        """Stop the LLM model and clean up resources."""
        try:
            self.running = False
            
            # Close any active sessions
            if hasattr(self, 'session') and self.session:
                await self.session.close()
                self.session = None
            
            # Clear any cached data
            if hasattr(self, 'last_request_time'):
                self.last_request_time = 0
                
            self.logger.info("LLM model stopped and resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error stopping LLM model: {e}")

    def is_healthy(self):
        """Check if the LLM is healthy."""
        if not self.running:
            return False
            
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response from the model.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            
        Returns:
            str: Generated response text
        """
        if not self.running:
            self.logger.error("LLM not running")
            await self.start()  # Attempt to start the LLM automatically
            if not self.running:
                return "Error: LLM service unavailable. Please check if Ollama is running."
            
        if not messages:
            self.logger.error("Empty messages list")
            return "Error: Empty messages list"
            
        # Optimize for fast model if using llama3.2:1b
        if self.model_name == "llama3.2:1b":
            # Reduce tokens for faster response
            self.max_tokens = min(self.max_tokens, 1024)
            # Use higher temperature for more creativity when responses are short
            self.temperature = 0.9
            
        # Prepare the request with model-specific settings
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False  # Disable streaming for now
        }
        
        # Retry logic with improved error handling
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Use short connection timeout but longer read timeout
                timeout = aiohttp.ClientTimeout(
                    connect=5,     # Connect timeout: 5 seconds
                    total=self.timeout  # Total timeout (including read)
                )
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    try:
                        # Log attempt for debugging
                        if attempt > 0:
                            self.logger.info(f"Retry attempt {attempt+1}/{self.max_retries} for Ollama request")
                            
                        start_time = time.time()
                        response = await session.post(
                            f"{self.base_url}/api/chat",
                            json=request_data,
                            headers={"Content-Type": "application/json"}
                        )
                        
                        # Log response time for performance monitoring
                        elapsed = time.time() - start_time
                        self.logger.info(f"Ollama response time: {elapsed:.2f}s (status: {response.status})")
                        
                        if response.status != 200:
                            error_msg = f"Error generating response: HTTP {response.status}"
                            if attempt < self.max_retries - 1:
                                self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                                await asyncio.sleep(0.5 * (attempt + 1))  # Shorter backoff for fast model
                                continue
                            else:
                                self.logger.error(error_msg)
                                return f"Error: Failed to generate response (status {response.status})"
                        
                        # Parse response with detailed error handling
                        try:
                            data = await response.json()
                            if isinstance(data, dict) and 'message' in data:
                                return data['message']['content']
                            else:
                                self.logger.error(f"Invalid response format: {data}")
                                return "Error: Received unexpected response format from LLM service"
                        except json.JSONDecodeError as e:
                            self.logger.error(f"Failed to parse JSON response: {e}")
                            return "Error: Received invalid response from LLM service"
                            
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

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm = LocalLLM(model_name="llama3.2:latest")
    
    if llm.start():
        print("LLM Model started successfully")
        
        # Test conversation
        conversation = [
            {"role": "system", "content": "You are a helpful AI assistant running entirely locally."},
            {"role": "user", "content": "Hello, can you introduce yourself?"}
        ]
        
        try:
            response = llm.generate_response(conversation)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            llm.stop()
    else:
        print("Failed to start LLM Model")
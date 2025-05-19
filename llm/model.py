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
    
    def __init__(self, model_name="ollama3.2:latest", host="localhost", port=11434):
        """
        Initialize the LLM interface.
        
        Args:
            model_name (str): Name of the Ollama model to use (ollama3.2:latest for chat, llava for screen sensor)
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
        self.min_request_interval = 1  # 1 second between requests
        self.timeout = 60  # Increased timeout to 60 seconds
        self.max_retries = 3  # Maximum number of retries
        
        # Configure model-specific settings
        if model_name == "llava":
            self.is_vision_model = True
            self.temperature = 0.7
            self.max_tokens = 1024
        else:  # ollama3.2:latest
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
            return "Error: LLM not running"
            
        if not messages:
            self.logger.error("Empty messages list")
            return "Error: Empty messages list"
            
        # Encode image
        try:
            image_base64 = self._encode_image(image)
        except Exception as e:
            self.logger.error(f"Error encoding image: {e}")
            return "Error: Failed to encode image"
            
        # Prepare request with image and optimized LLaVA prompt
        prompt_messages = messages.copy()
        
        # Enhance system prompt for better image analysis if it exists
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
                break
        
        # Prepare the request with enhanced prompting
        request_data = {
            "model": self.model_name,
            "messages": prompt_messages,
            "images": [image_base64],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        
        # Retry logic for reliability
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    try:
                        response = await session.post(
                            f"{self.base_url}/api/chat",
                            json=request_data,
                            timeout=self.timeout
                        )
                        
                        if response.status != 200:
                            error_msg = f"Error generating response: {response.status}"
                            if attempt < self.max_retries - 1:
                                self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                                continue
                            else:
                                self.logger.error(error_msg)
                                return f"Error: Failed to generate response (status {response.status})"
                        
                        data = await response.json()
                        if isinstance(data, dict) and 'message' in data:
                            return data['message']['content']
                        else:
                            self.logger.error("Invalid response format")
                            return "Error: Invalid response format"
                            
                    except asyncio.TimeoutError:
                        if attempt < self.max_retries - 1:
                            self.logger.warning(f"Request timed out, retrying ({attempt+1}/{self.max_retries})")
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                        else:
                            self.logger.error("Request timed out after all retries")
                            return "Error: Request timed out"
                            
            except Exception as e:
                self.logger.error(f"Error in generate_response_with_image: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                else:
                    return f"Error: {str(e)}"
                    
        return "Error: Failed to generate response after all retries"
    
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
        """Stop the LLM model."""
        self.running = False

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
            return "Error: LLM not running"
            
        if not messages:
            self.logger.error("Empty messages list")
            return "Error: Empty messages list"
            
        # Prepare the request with model-specific settings
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # Retry logic for reliability
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    try:
                        response = await session.post(
                            f"{self.base_url}/api/chat",
                            json=request_data,
                            timeout=self.timeout
                        )
                        
                        if response.status != 200:
                            error_msg = f"Error generating response: {response.status}"
                            if attempt < self.max_retries - 1:
                                self.logger.warning(f"{error_msg}, retrying ({attempt+1}/{self.max_retries})")
                                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                                continue
                            else:
                                self.logger.error(error_msg)
                                return f"Error: Failed to generate response (status {response.status})"
                        
                        data = await response.json()
                        if isinstance(data, dict) and 'message' in data:
                            return data['message']['content']
                        else:
                            self.logger.error("Invalid response format")
                            return "Error: Invalid response format"
                            
                    except asyncio.TimeoutError:
                        if attempt < self.max_retries - 1:
                            self.logger.warning(f"Request timed out, retrying ({attempt+1}/{self.max_retries})")
                            await asyncio.sleep(1 * (attempt + 1))
                            continue
                        else:
                            self.logger.error("Request timed out after all retries")
                            return "Error: Request timed out"
                            
            except Exception as e:
                self.logger.error(f"Error in generate_response: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                else:
                    return f"Error: {str(e)}"
                    
        return "Error: Failed to generate response after all retries"

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm = LocalLLM(model_name="ollam3.2:latest")
    
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
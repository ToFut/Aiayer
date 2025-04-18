"""
Local LLM Integration Module
Provides interface to local language models via Ollama.
"""
import os
import json
import logging
import aiohttp
import asyncio
from collections import deque
from typing import List, Dict

import requests

class LocalLLM:
    """
    Interface to a locally running language model via Ollama.
    Provides methods to ensure model availability and generate responses.
    """ 
    
    def __init__(self, model_name="mistral:latest", host="localhost", port=11434):
        """
        Initialize the LLM interface.
        
        Args:
            model_name (str): Name of the Ollama model to use
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
                
                models = [model['name'] for model in await response.json().get('models', [])]
                
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
                
                models = [model['name'] for model in await response.json().get('models', [])]
                
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
            
    async def generate_response(self, messages: List[Dict[str, str]], context_data=None) -> str:
        """
        Generate a response from the model.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            context_data (Dict, optional): Additional context data to use for the response
            
        Returns:
            str: Generated response text
        """
        if not self.running:
            self.logger.error("LLM not running")
            return "Error: LLM not running"
            
        if not messages:
            self.logger.error("Empty messages list")
            return "Error: Empty messages list"
            
        # Validate messages
        for message in messages:
            if not isinstance(message, dict):
                self.logger.error("Invalid message format")
                return "Error: Invalid message format"
                
            if 'role' not in message or 'content' not in message:
                self.logger.error("Message missing required fields")
                return "Error: Message missing required fields"
                
            if message['content'] is None:
                self.logger.error("Message content is None")
                return "Error: Message content is None"
                
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": messages
                    },
                    timeout=self.timeout
                )
                
                if response.status != 200:
                    self.logger.error(f"Error generating response: {response.status}")
                    return f"Error: Failed to generate response (status {response.status})"
                
                data = await response.json()
                if isinstance(data, dict) and 'message' in data:
                    return data['message'].get('content', '')
                elif isinstance(data, str):
                    return data
                else:
                    self.logger.error(f"Unexpected response format: {data}")
                    return "Error: Unexpected response format"
        
        except asyncio.CancelledError:
            self.logger.error("Request cancelled during model generation")
            return "I'm sorry, but my request was cancelled. Please try again."
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"I'm sorry, I encountered an error: {str(e)}. Please try again later."

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm = LocalLLM(model_name="mistral:latest")
    
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
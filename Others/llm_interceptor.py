#!/usr/bin/env python3
"""
LLM Interceptor Module

This module provides a fallback mechanism for LLM requests that ensures
responses are always provided within a reasonable timeframe.
"""
import asyncio
import json
import logging
import random
import aiohttp
import os
import sys
from typing import List, Dict

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm_interceptor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class InterceptorLLM:
    """
    LLM interceptor that ensures responses are always provided,
    even if the actual LLM service times out.
    """
    
    def __init__(self, model_name="llama3.2:latest", host="localhost", port=11434):
        """
        Initialize the LLM interceptor.
        
        Args:
            model_name (str): Name of the Ollama model to use
            host (str): Hostname where Ollama API is running
            port (int): Port for Ollama API
        """
        self.model_name = model_name
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.running = True
        self.timeout = 30  # 30 second timeout
        
        # Fallback responses for different query types
        self.fallback_responses = {
            "examples": [
                "I can help you with monitoring your screen content, tracking application processes, and providing context-aware assistance. I can analyze what's on your screen, understand your work context, and offer relevant information.",
                "The system can monitor your screen, track running applications, and provide contextual assistance. It uses AI to understand your work environment and help you with relevant information and suggestions.",
                "I can demonstrate capabilities like screen content analysis, process monitoring, and context-aware assistance. The system understands what you're working on and provides relevant information based on your current context."
            ],
            "help": [
                "I can assist you with understanding your screen content, monitoring running applications, and providing context-based assistance. What specific help do you need?",
                "This AI assistant can help you by analyzing your screen, tracking your active programs, and offering contextual assistance. How can I help you specifically?",
                "I'm designed to assist with context-aware tasks by monitoring your screen and running applications. I can provide relevant information based on what you're currently doing."
            ],
            "how_works": [
                "This system works by collecting data from various sensors that monitor your screen content and running processes. It uses this context to provide more relevant assistance tailored to what you're doing.",
                "The system uses screen and process sensors to understand your current context. It then uses this information to provide more relevant and helpful responses based on what you're working on.",
                "This AI assistant monitors your screen content and running applications to understand your work context. This information helps it provide more relevant assistance and suggestions."
            ],
            "default": [
                "I'm your AI assistant designed to understand your work context and provide relevant assistance. I can monitor your screen, track applications, and help with various tasks.",
                "I'm here to assist you with your work by understanding your context and providing relevant information. I can analyze what's on your screen and what applications you're using to offer better assistance.",
                "As your AI assistant, I can help you with various tasks by understanding your current context. I monitor your screen and running applications to provide more relevant assistance."
            ]
        }
        
        logger.info(f"LLM Interceptor initialized with model: {model_name}")
    
    def get_fallback_response(self, query):
        """Generate an appropriate fallback response based on the query content."""
        query_lower = query.lower()
        
        # Check for query patterns
        if any(kw in query_lower for kw in ["example", "show me", "what can you do"]):
            return random.choice(self.fallback_responses["examples"])
        elif any(kw in query_lower for kw in ["help", "assist"]):
            return random.choice(self.fallback_responses["help"])
        elif any(kw in query_lower for kw in ["how", "work"]):
            return random.choice(self.fallback_responses["how_works"])
        else:
            return random.choice(self.fallback_responses["default"])
    
    async def initialize(self):
        """
        Initialize the LLM interceptor.
        """
        logger.info("Initializing LLM interceptor")
        try:
            # Check if Ollama is available
            async with aiohttp.ClientSession() as session:
                try:
                    response = await asyncio.wait_for(
                        session.get(f"{self.base_url}/api/version"),
                        timeout=5
                    )
                    
                    if response.status == 200:
                        logger.info("Successfully connected to Ollama")
                        
                        # Try to ensure model is available
                        try:
                            await self.ensure_model_available()
                        except Exception as model_e:
                            logger.warning(f"Could not ensure model availability: {model_e}")
                    else:
                        logger.warning(f"Ollama returned status {response.status}")
                except Exception as e:
                    logger.warning(f"Could not connect to Ollama: {e}")
            
            return self
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            self.running = False
            # Don't raise, still allow the interceptor to function
            return self
    
    async def ensure_model_available(self):
        """
        Ensure the model is available, but don't fail if it's not.
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Check if model is available
                response = await asyncio.wait_for(
                    session.get(f"{self.base_url}/api/tags"),
                    timeout=5
                )
                
                if response.status != 200:
                    logger.warning("Could not get model list")
                    return
                
                data = await response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                if self.model_name not in models:
                    logger.info(f"Model {self.model_name} not found, will try to pull it")
                    
                    try:
                        pull_response = await asyncio.wait_for(
                            session.post(
                                f"{self.base_url}/api/pull",
                                json={"name": self.model_name}
                            ),
                            timeout=30  # Longer timeout for model pull
                        )
                        
                        if pull_response.status == 200:
                            logger.info(f"Successfully pulled model {self.model_name}")
                        else:
                            logger.warning(f"Failed to pull model: {pull_response.status}")
                    except Exception as pull_e:
                        logger.warning(f"Error pulling model: {pull_e}")
                
                else:
                    logger.info(f"Model {self.model_name} is available")
        
        except Exception as e:
            logger.warning(f"Error ensuring model availability: {e}")
    
    async def generate_response(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response with interceptor logic.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            
        Returns:
            str: Generated response text
        """
        if not messages:
            return "I didn't receive a valid query to respond to."
        
        # Extract the query from messages
        query = ""
        for msg in messages:
            if msg.get('role') == 'user':
                query = msg.get('content', '')
                break
        
        # If no user message found, use the last message
        if not query and messages:
            query = messages[-1].get('content', '')
        
        # Try to get a response from the actual LLM
        llm_response = await self._try_real_llm(messages)
        
        # If we got a valid response, return it
        if llm_response and not llm_response.startswith("Error:"):
            logger.info("Using real LLM response")
            return llm_response
        
        # Otherwise, provide a fallback response
        logger.info("Using fallback response")
        return self.get_fallback_response(query)
    
    async def _try_real_llm(self, messages: List[Dict[str, str]]) -> str:
        """
        Try to get a response from the real LLM service.
        
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries
            
        Returns:
            str: Response text or None if failed
        """
        try:
            request_data = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            async with aiohttp.ClientSession() as session:
                try:
                    response = await asyncio.wait_for(
                        session.post(
                            f"{self.base_url}/api/chat",
                            json=request_data
                        ),
                        timeout=self.timeout
                    )
                    
                    if response.status != 200:
                        logger.warning(f"LLM request failed with status {response.status}")
                        return None
                    
                    data = await response.json()
                    if isinstance(data, dict) and 'message' in data:
                        return data['message']['content']
                    else:
                        logger.warning("Invalid response format from LLM")
                        return None
                
                except asyncio.TimeoutError:
                    logger.warning(f"LLM request timed out after {self.timeout} seconds")
                    return None
                
                except Exception as e:
                    logger.warning(f"Error making LLM request: {e}")
                    return None
        
        except Exception as e:
            logger.error(f"Unexpected error in _try_real_llm: {e}")
            return None

# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        interceptor = InterceptorLLM()
        await interceptor.initialize()
        
        test_messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Show me some examples of what you can do."}
        ]
        
        response = await interceptor.generate_response(test_messages)
        print(f"Response: {response}")
    
    asyncio.run(test())
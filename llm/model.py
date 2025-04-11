"""
Local LLM Integration Module
Provides interface to local language models via Ollama.
"""
import os
import json
import logging
import requests
import time
from collections import deque

class LocalLLM:
    """
    Interface to a locally running language model via Ollama.
    Provides methods to ensure model availability and generate responses.
    """
    
    def __init__(self, model_name="mistral", host="localhost", port=11434):
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
        
    def start(self):
        """Start the LLM model."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code != 200:
                self.logger.error("Failed to connect to Ollama")
                return False
                
            self.logger.info(f"Connected to Ollama version: {response.json().get('version')}")
            
            # Check if model is available
            response = requests.get(f"{self.base_url}/api/tags")
            models = [model['name'] for model in response.json().get('models', [])]
            
            if self.model_name not in models:
                self.logger.info(f"Model {self.model_name} not found, pulling...")
                response = requests.post(
                    f"{self.base_url}/api/pull",
                    json={"name": self.model_name},
                    stream=True
                )
                if response.status_code != 200:
                    self.logger.error("Failed to pull model")
                    return False
                    
            self.running = True
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting LLM: {e}")
            return False
            
    def stop(self):
        """Stop the LLM model."""
        self.running = False
        return True
        
    def is_healthy(self):
        """Check if the LLM is healthy."""
        if not self.running:
            return False
            
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=2)
            return response.status_code == 200
        except:
            return False
            
    def generate_response(self, conversation, timeout=30):
        """Generate a response using the model."""
        try:
            if not self.running:
                if not self.start():
                    return "Error: Could not start LLM service"
                    
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval)
            self.last_request_time = current_time
            
            # Format prompt from conversation
            prompt = ""
            for msg in conversation:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    prompt += f"Assistant: {msg['content']}\n\n"
            
            prompt += "Assistant:"
            
            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 100,
                    }
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if "response" in result:
                    return result["response"].strip()
                    
            self.logger.error(f"Error from Ollama API: {response.text}")
            return "Error: Failed to generate response"
            
        except requests.exceptions.Timeout:
            self.logger.error("Request timed out")
            return "Error: Request timed out"
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error")
            return "Error: Could not connect to LLM service"
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return f"Error: {str(e)}"

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    llm = LocalLLM(model_name="mistral")
    
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
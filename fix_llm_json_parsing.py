#!/usr/bin/env python3
"""
Fix LLM JSON Parsing Issues
This script applies a fix to handle application/x-ndjson content type
from Ollama API correctly.
"""

import logging
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def patch_llm_model():
    """Apply fixes to the LLM model.py file to handle NDJSON correctly"""
    model_file_path = os.path.join(os.getcwd(), 'llm', 'model.py')
    
    if not os.path.exists(model_file_path):
        logger.error(f"Could not find model.py at {model_file_path}")
        return False
    
    # Create backup
    backup_path = model_file_path + '.bak'
    try:
        with open(model_file_path, 'r') as f:
            original_content = f.read()
        
        with open(backup_path, 'w') as f:
            f.write(original_content)
        logger.info(f"Created backup at {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False
    
    # Apply fix for generate_response method
    try:
        # The fix involves modifying the response handling for application/x-ndjson
        # Look for the pattern where it tries to call response.json() directly
        json_parser_pattern = r'(async def generate_response.*?try:.*?data = await response\.json\(\))'
        
        # Define the fixed pattern that will detect and handle ndjson correctly
        fixed_pattern = '''async def generate_response(self, messages, stream=False, temperature=0.7, max_tokens=None):
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
            self.logger.error("LLM not running")
            try:
                await self.start()
            except Exception as e:
                self.logger.error(f"Failed to start LLM: {e}")
                return "Error: LLM service not available"
        
        # Rate limit requests
        current_time = time.time()
        if current_time - self.last_request_time < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - (current_time - self.last_request_time))
        self.last_request_time = time.time()
        
        request_data = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "temperature": temperature
        }
        
        if max_tokens is not None:
            request_data["max_tokens"] = max_tokens
        
        start_time = time.time()
        
        # Implement retry logic
        for attempt in range(self.max_retries):
            try:
                async with get_http_session() as session:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=request_data,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
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
                        
                        # Parse response with detailed error handling
                        try:
                            # Check content type to determine how to parse the response
                            content_type = response.headers.get('Content-Type', '')
                            
                            if 'application/x-ndjson' in content_type:
                                # FIXED: Always handle streaming responses properly
                                text = await response.text()
                                
                                # Get the last non-empty line for final response
                                lines = [line for line in text.split('\\n') if line.strip()]
                                if not lines:
                                    self.logger.error("Empty NDJSON response")
                                    return "Error: Received empty response from LLM service"
                                
                                # For streaming response, we need to concatenate all the content parts
                                full_response = ""
                                for line in lines:
                                    try:
                                        data = json.loads(line)
                                        if 'message' in data and 'content' in data['message']:
                                            full_response += data['message']['content']
                                    except json.JSONDecodeError as e:
                                        self.logger.warning(f"Failed to parse JSON line: {e}")
                                        continue
                                
                                self.logger.info(f"Ollama response time: {time.time() - start_time:.2f}s (status: {response.status})")
                                return full_response
                            else:
                                # For regular JSON response
                                try:
                                    data = await response.json()'''
        
        # Replace the method with our fixed version
        modified_content = re.sub(json_parser_pattern, fixed_pattern, original_content, flags=re.DOTALL)
        
        # Check if the pattern was found and replaced
        if modified_content == original_content:
            logger.warning("Could not find the pattern to replace in model.py")
            return False
        
        # Write the modified content back to the file
        with open(model_file_path, 'w') as f:
            f.write(modified_content)
        
        logger.info("✅ Successfully applied fix to model.py")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply fix: {e}")
        return False

def main():
    """Apply the LLM JSON parsing fix"""
    logger.info("Applying fix for LLM JSON parsing issues...")
    
    if patch_llm_model():
        logger.info("✅ Successfully patched LLM model to handle NDJSON correctly")
        logger.info("To apply the fix, restart the system: ./RESTART_FIXED_SYSTEM.sh")
    else:
        logger.error("❌ Failed to patch LLM model")
        logger.info("You can try manual fixes as described in the documentation")

if __name__ == "__main__":
    main()
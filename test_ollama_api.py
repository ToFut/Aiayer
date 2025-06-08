#!/usr/bin/env python3
import asyncio
import logging
import sys
from llm.model import OllamaLLM

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ollama_api_test")

async def test_text_generation():
    """Test the text generation API with simple prompts"""
    logger.info("Testing Ollama text generation API")
    
    try:
        # Use context manager for automatic cleanup
        async with OllamaLLM() as llm:
            # Simple test messages
            messages = [
                {"role": "user", "content": "What is the capital of France?"}
            ]
            
            # Test the generate_response method
            response = await llm.generate_response(messages)
            logger.info(f"Successfully received response: {response[:100]}...")  # Log first 100 chars
            
            # Test with system message
            messages_with_system = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What's the tallest mountain in the world?"}
            ]
            
            response = await llm.generate_response(messages_with_system)
            logger.info(f"Response with system message: {response[:100]}...")
            
            return True
    except Exception as e:
        logger.error(f"Error testing text generation: {str(e)}")
        return False

async def main():
    """Run all tests"""
    text_success = await test_text_generation()
    
    if text_success:
        logger.info("All tests completed successfully!")
    else:
        logger.error("Tests failed")
    
    # We don't need to manually close sessions anymore since we're using context managers

if __name__ == "__main__":
    asyncio.run(main())
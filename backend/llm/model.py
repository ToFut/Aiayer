import time
import logging
from typing import Optional

class LLMModel:
    def __init__(self):
        self.timeout = 30  # Increased from 20s to 30s
        self.max_retries = 3
        self.base_delay = 1  # Base delay in seconds

    async def generate_response(self, prompt: str) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                # Calculate delay with exponential backoff
                delay = self.base_delay * (2 ** attempt)
                if attempt > 0:
                    logging.info(f"Retry attempt {attempt + 1}/{self.max_retries} after {delay}s delay")
                    await asyncio.sleep(delay)
                
                # Your existing LLM call logic here
                response = await self._call_llm(prompt)
                return response
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Request timed out after {self.timeout}s after all retries")
                    raise
                logging.warning(f"Request timed out after {self.timeout}s, retrying ({attempt + 1}/{self.max_retries})")

    async def _call_llm(self, prompt: str) -> str:
        # Your existing LLM implementation
        pass 
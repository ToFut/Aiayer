
import asyncio
import aiohttp
from collections import deque
import json
import time

class LLMRequestQueue:
    def __init__(self, max_concurrent=1):
        self.max_concurrent = max_concurrent
        self.active_requests = 0
        self.queue = deque()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def make_request(self, payload):
        async with self.semaphore:
            self.active_requests += 1
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "http://localhost:11434/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        result = await response.json()
                        return result
            finally:
                self.active_requests -= 1

# Global queue instance
llm_queue = LLMRequestQueue(max_concurrent=1)

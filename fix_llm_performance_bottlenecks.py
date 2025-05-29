#!/usr/bin/env python3
"""
Quick fixes for LLM performance bottlenecks
"""

import subprocess
import psutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llm_fix')

def restart_ollama_service():
    """Restart Ollama to clear memory and reset connections"""
    logger.info("🔄 Restarting Ollama service...")
    try:
        # Kill Ollama processes
        subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
        logger.info("   Killed existing Ollama processes")
        
        # Wait a moment
        import time
        time.sleep(3)
        
        # Start Ollama
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("   Started new Ollama service")
        
        # Wait for startup
        time.sleep(5)
        
        # Test if it's working
        result = subprocess.run(["curl", "-s", "http://localhost:11434/api/version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ Ollama service restarted successfully")
            return True
        else:
            logger.error("❌ Ollama service failed to start")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to restart Ollama: {e}")
        return False

def free_system_memory():
    """Free up system memory"""
    logger.info("🧹 Freeing system memory...")
    
    try:
        # Get memory info
        memory = psutil.virtual_memory()
        logger.info(f"   Current memory usage: {memory.percent:.1f}%")
        
        if memory.percent > 80:
            logger.warning("   High memory usage detected")
            
            # Find memory-heavy processes (excluding system processes)
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cmdline']):
                try:
                    if proc.info['memory_percent'] > 5:  # >5% memory usage
                        processes.append(proc.info)
                except:
                    continue
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            logger.info("   Top memory consumers:")
            for proc in processes[:5]:
                logger.info(f"     {proc['name']}: {proc['memory_percent']:.1f}%")
        
        # Force garbage collection
        import gc
        gc.collect()
        
        logger.info("✅ Memory cleanup completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory cleanup failed: {e}")
        return False

def limit_concurrent_llm_requests():
    """Create a simple request queue to limit concurrent LLM requests"""
    logger.info("🚦 Setting up LLM request limiting...")
    
    queue_script = '''
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
'''
    
    try:
        # Write the queue script
        with open('llm_request_queue.py', 'w') as f:
            f.write(queue_script)
        
        logger.info("✅ LLM request queue created")
        logger.info("   This limits to 1 concurrent LLM request")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create request queue: {e}")
        return False

def main():
    """Apply all performance fixes"""
    logger.info("🚀 Applying LLM Performance Fixes")
    logger.info("=" * 50)
    
    fixes_applied = 0
    
    # 1. Free memory
    if free_system_memory():
        fixes_applied += 1
    
    # 2. Restart Ollama
    if restart_ollama_service():
        fixes_applied += 1
    
    # 3. Create request limiting
    if limit_concurrent_llm_requests():
        fixes_applied += 1
    
    logger.info("")
    logger.info("=" * 50)
    logger.info(f"📊 Applied {fixes_applied}/3 performance fixes")
    
    if fixes_applied >= 2:
        logger.info("✅ Performance should be significantly improved!")
        logger.info("")
        logger.info("🧪 Test improvements with:")
        logger.info("   python3 test_spotify_agent_fix.py")
        logger.info("   python3 quick_llm_speed_fix.py")
        logger.info("")
        logger.info("💡 Additional recommendations:")
        logger.info("   - Close unnecessary applications to free memory")
        logger.info("   - Use simpler prompts during testing")
        logger.info("   - Avoid sending multiple requests simultaneously")
    else:
        logger.warning("⚠️  Some fixes failed - manual intervention may be needed")
        logger.info("")
        logger.info("🔧 Manual fixes:")
        logger.info("   1. Restart Ollama: sudo pkill ollama && ollama serve")
        logger.info("   2. Close memory-heavy applications")
        logger.info("   3. Restart the backend system")

if __name__ == "__main__":
    main()
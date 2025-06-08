#!/usr/bin/env python3
"""
Start Memory Trigger Service

This script explicitly starts the memory trigger service to monitor memory
and generate notifications.
"""

import asyncio
import logging
import sys
import os
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_trigger_startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory_trigger_startup")

async def start_memory_trigger_service():
    """Start the memory trigger service"""
    try:
        # Import memory trigger service
        from memory.memory_trigger_service import MemoryTriggerService
        from memory.memory_system import MemorySystem
        
        # Create memory system
        memory_system = MemorySystem()
        logger.info("Created memory system")
        
        # Create memory trigger service
        trigger_service = MemoryTriggerService(memory_system=memory_system)
        logger.info("Created memory trigger service")
        
        # Start service
        await trigger_service.start()
        logger.info("Started memory trigger service")
        
        # Keep the service running
        while True:
            logger.info(f"Memory trigger service running... (PID: {os.getpid()})")
            await asyncio.sleep(60)
            
    except Exception as e:
        logger.error(f"Error starting memory trigger service: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    logger.info("🚀 Starting memory trigger service")
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs/memory', exist_ok=True)
    
    # Start memory trigger service
    await start_memory_trigger_service()
    
    return True

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Memory trigger service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
#!/usr/bin/env python3
"""
Start Memory System
Initializes and starts all memory system components.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_system')

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def start_memory_system():
    """Start the memory system and its components."""
    try:
        # Import required modules
        from memory.memory_system import MemorySystem
        from memory.update_conscious import update_conscious_memory
        from sensors.process_sensor import ProcessSensor
        
        # Initialize memory system
        logger.info("Initializing memory system...")
        memory_system = MemorySystem()
        
        # Initialize process sensor with config
        process_config = {
            "update_interval": 5,  # Update every 5 seconds
            "max_processes": 10,   # Track top 10 processes
            "track_resources": True  # Track CPU and memory usage
        }
        process_sensor = ProcessSensor(config=process_config)
        memory_system.process_sensor = process_sensor
        
        # Initialize the memory system
        await memory_system.initialize()
        
        logger.info("Memory system initialized successfully")
        
        # Start conscious memory updates
        logger.info("Starting conscious memory updates...")
        while True:
            try:
                conscious = update_conscious_memory()
                if conscious:
                    logger.info("Conscious memory updated successfully")
                else:
                    logger.warning("Failed to update conscious memory")
                    
                # Wait before next update
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error updating conscious memory: {e}")
                await asyncio.sleep(5)  # Wait before retry
                
    except Exception as e:
        logger.error(f"Error starting memory system: {e}")
        return False
        
    return True

async def demo_memory_feeding(memory_system):
    while True:
        # Add to short-term
        content_short = f'Demo short-term {random.randint(1,1000)}'
        await memory_system.add_to_short_term_memory({
            'content': content_short,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"[DEMO] Added to short-term: {content_short[:30]}")
        # Add to long-term
        content_long = f'Demo long-term {random.randint(1,1000)}'
        await memory_system.add_to_long_term_memory({
            'content': content_long,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"[DEMO] Added to long-term: {content_long[:30]}")
        # Add to context
        content_context = f'Demo context {random.randint(1,1000)}'
        await memory_system.add_to_context_memory({
            'content': content_context,
            'timestamp': datetime.now().isoformat()
        })
        logger.info(f"[DEMO] Added to context: {content_context[:30]}")
        await asyncio.sleep(15)  # Adjust interval as needed

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Start the memory system
    logger.info("Starting memory system...")
    async def main():
        from memory.memory_system import MemorySystem
        memory_system = MemorySystem()
        await memory_system.initialize()
        # Start demo feeding in parallel
        asyncio.create_task(demo_memory_feeding(memory_system))
        # Keep the main loop running
        while True:
            await asyncio.sleep(10)
    asyncio.run(main()) 
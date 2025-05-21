#!/usr/bin/env python3
"""
Run Enhanced Context Memory System
Starts the enhanced context memory system with LLaVA visual analysis,
process classification, and contextual relationship tracking.
"""
import os
import asyncio
import logging
import time
import signal
import sys
import json
from datetime import datetime

# Import components
from llava_visual_processor import LLaVAVisualProcessor
from enhanced_context_memory import EnhancedContextMemory
from memory_context_integration import MemoryContextIntegration
from memory.memory_system import MemorySystem
from sensors.fixed_screen_sensor import FixedScreenSensor
from sensors.fixed_process_sensor import FixedProcessSensor

# Configure logging
os.makedirs('logs/system', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system/enhanced_context_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_memory_system')

# Global variables for signal handling
running = True
tasks = []

def signal_handler(sig, frame):
    """Handle termination signals"""
    global running
    logger.info("Received termination signal")
    running = False

async def main():
    """Main function"""
    global running, tasks
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create PIDs directory
    os.makedirs('pids', exist_ok=True)
    
    # Save PID
    pid = os.getpid()
    with open('pids/enhanced_context_memory.pid', 'w') as f:
        f.write(str(pid))
    logger.info(f"Process ID: {pid}")

    try:
        # Initialize components
        logger.info("Initializing components...")
        
        # Initialize memory system
        memory_system = MemorySystem()
        await memory_system.initialize()
        logger.info("Memory system initialized")
        
        # Initialize LLaVA processor
        llava_processor = LLaVAVisualProcessor()
        logger.info("LLaVA processor initialized")
        
        # Initialize enhanced context memory
        enhanced_context = EnhancedContextMemory(
            memory_system=memory_system,
            llava_processor=llava_processor
        )
        logger.info("Enhanced context memory initialized")
        
        # Initialize memory context integration
        integration = MemoryContextIntegration(memory_system)
        await integration.start()
        logger.info("Memory context integration started")
        
        # Initialize sensors
        screen_sensor = FixedScreenSensor()
        if not await screen_sensor.initialize():
            logger.error("Failed to initialize screen sensor")
            return
        
        process_sensor = FixedProcessSensor()
        await process_sensor.initialize()
        logger.info("Sensors initialized")
        
        # Create output directories
        os.makedirs('results', exist_ok=True)
        
        # Main processing loop
        logger.info("Starting main loop")
        
        while running:
            try:
                # Capture screen data
                screen_data = await screen_sensor.get_current_state()
                
                # Add to context integration
                await integration.add_sensor_data('screen', screen_data)
                
                # Capture process data
                process_data = await process_sensor.get_current_state()
                
                # Add to context integration
                await integration.add_sensor_data('process', process_data)
                
                # Get enhanced context
                context = await integration.get_enhanced_context()
                
                # Save context snapshot periodically
                timestamp = int(time.time())
                if timestamp % 60 == 0:  # Every minute
                    snapshot_file = f'results/context_snapshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                    with open(snapshot_file, 'w') as f:
                        json.dump(context, f, indent=2)
                    logger.info(f"Saved context snapshot to {snapshot_file}")
                
                # Sleep between iterations
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                logger.exception("Exception details")
                await asyncio.sleep(5)  # Wait longer on error
        
        # Shutdown
        logger.info("Shutting down...")
        
        # Stop integration
        await integration.stop()
        
        # Clean up sensors
        await screen_sensor.cleanup()
        await process_sensor.cleanup()
        
        logger.info("System shutdown complete")
    
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.exception("Exception details")
    
    finally:
        # Ensure cleanup happens
        for task in tasks:
            if not task.done():
                task.cancel()
        
        # Remove PID file
        if os.path.exists('pids/enhanced_context_memory.pid'):
            os.remove('pids/enhanced_context_memory.pid')

if __name__ == "__main__":
    asyncio.run(main())
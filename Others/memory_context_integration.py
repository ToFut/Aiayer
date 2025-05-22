#!/usr/bin/env python3
"""
Memory Context Integration Module
Connects the enhanced context memory system with the existing memory system.
"""
import asyncio
import logging
import os
import time
import traceback
from typing import Dict, Any, Optional

# Import enhanced components
from llava_visual_processor import LLaVAVisualProcessor
from enhanced_context_memory import EnhancedContextMemory

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/memory_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('memory_integration')

class MemoryContextIntegration:
    """
    Integrates the enhanced context memory system with the existing memory system.
    Acts as a middleware to enhance sensor data with visual understanding and
    contextual relationships before passing it to the main memory system.
    """
    
    def __init__(self, memory_system, ollama_url="http://localhost:11434"):
        self.memory_system = memory_system
        
        # Initialize LLaVA processor
        logger.info("Initializing LLaVA visual processor")
        self.llava_processor = LLaVAVisualProcessor(ollama_url=ollama_url)
        
        # Initialize enhanced context memory
        logger.info("Initializing enhanced context memory")
        self.enhanced_context = EnhancedContextMemory(
            memory_system=memory_system, 
            llava_processor=self.llava_processor
        )
        
        # Processing queue
        self.processing_queue = {
            'screen': asyncio.Queue(),
            'process': asyncio.Queue(),
            'file': asyncio.Queue()
        }
        
        # Processing tasks
        self.tasks = {}
        
        # Status
        self.running = False
        
        logger.info("Memory context integration initialized")
    
    async def start(self):
        """Start the integration service"""
        if self.running:
            logger.warning("Integration service already running")
            return
            
        logger.info("Starting memory context integration")
        self.running = True
        
        # Create processing tasks for each sensor type
        self.tasks['screen'] = asyncio.create_task(self._process_queue('screen'))
        self.tasks['process'] = asyncio.create_task(self._process_queue('process'))
        self.tasks['file'] = asyncio.create_task(self._process_queue('file'))
        
        logger.info("Memory context integration started")
    
    async def stop(self):
        """Stop the integration service"""
        if not self.running:
            logger.warning("Integration service not running")
            return
            
        logger.info("Stopping memory context integration")
        self.running = False
        
        # Cancel all tasks
        for sensor_type, task in self.tasks.items():
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.tasks = {}
        logger.info("Memory context integration stopped")
    
    async def add_sensor_data(self, sensor_type: str, data: Dict[str, Any]) -> bool:
        """
        Add sensor data to the processing queue
        
        Args:
            sensor_type: Type of sensor data (screen, process, file)
            data: The sensor data to process
            
        Returns:
            Success flag
        """
        try:
            if not sensor_type or not data:
                logger.error(f"Invalid sensor data: {sensor_type}")
                return False
                
            if sensor_type not in self.processing_queue:
                logger.error(f"Unknown sensor type: {sensor_type}")
                return False
                
            # Add timestamp if missing
            if 'timestamp' not in data:
                data['timestamp'] = time.time()
                
            # Add to processing queue
            await self.processing_queue[sensor_type].put(data)
            logger.info(f"Added {sensor_type} data to processing queue")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding sensor data to queue: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def _process_queue(self, sensor_type: str):
        """
        Process the queue for a specific sensor type
        
        Args:
            sensor_type: Type of sensor data to process
        """
        logger.info(f"Started processing queue for {sensor_type}")
        
        try:
            while self.running:
                # Get item from queue
                try:
                    data = await asyncio.wait_for(
                        self.processing_queue[sensor_type].get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    # No data in queue, continue loop
                    continue
                    
                # Process the data
                try:
                    logger.info(f"Processing {sensor_type} data")
                    
                    # Send to enhanced context memory for processing
                    await self.enhanced_context.add_sensor_data(sensor_type, data)
                    
                    # Mark task as done
                    self.processing_queue[sensor_type].task_done()
                    
                except Exception as e:
                    logger.error(f"Error processing {sensor_type} data: {e}")
                    logger.error(traceback.format_exc())
                    # Still mark as done even if processing failed
                    self.processing_queue[sensor_type].task_done()
                    
        except asyncio.CancelledError:
            logger.info(f"Processing queue for {sensor_type} cancelled")
            
        except Exception as e:
            logger.error(f"Unexpected error in {sensor_type} processing queue: {e}")
            logger.error(traceback.format_exc())
    
    async def get_enhanced_context(self) -> Dict[str, Any]:
        """
        Get the current enhanced context for LLM consumption
        
        Returns:
            Dict with current context
        """
        return await self.enhanced_context.get_current_context()

# Main function for testing
async def main():
    """Test the memory context integration"""
    # Mock memory system for testing
    class MockMemorySystem:
        async def add_sensor_data(self, sensor_type, data):
            print(f"Adding {sensor_type} data to memory system")
            return True
    
    # Create mock memory system
    memory_system = MockMemorySystem()
    
    # Create integration
    integration = MemoryContextIntegration(memory_system)
    
    # Start the service
    await integration.start()
    
    try:
        # Add test data
        print("Adding test screen data")
        await integration.add_sensor_data("screen", {
            "active_window": "Test Window",
            "timestamp": time.time()
        })
        
        print("Adding test process data")
        await integration.add_sensor_data("process", {
            "active_apps": ["Test App", "Background Process"],
            "active_window": "Test Window",
            "timestamp": time.time()
        })
        
        # Wait for processing
        print("Waiting for processing...")
        await asyncio.sleep(2)
        
        # Get enhanced context
        context = await integration.get_enhanced_context()
        print("Enhanced context:")
        import json
        print(json.dumps(context, indent=2))
        
    finally:
        # Stop the service
        await integration.stop()

if __name__ == "__main__":
    asyncio.run(main())
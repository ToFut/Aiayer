"""
Simple test for web content notification.
"""
import sys
import asyncio
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_web_notification")

async def main():
    """Main test function"""
    try:
        # Import memory components
        from memory.memory_system import MemorySystem
        
        # Create memory system instance
        memory_system = MemorySystem()
        logger.info("Created memory system")
        
        # Add web content memory item
        web_memory = {
            "type": "web_content",
            "url": "https://www.example.com/shopping",
            "title": "Example Shopping Page",
            "searchable_text": """
            Welcome to our Online Store
            
            Today's Deals:
            - Smartphone XYZ - $799.99 (20% off)
            - Wireless Headphones - $149.99
            - Smart Watch - $249.99
            
            Add to Cart | Buy Now | Checkout
            
            Free shipping on orders over $50
            """,
            "timestamp": time.time(),
            "source": "web_browser"
        }
        
        # Add to memory
        memory_system.short_term_memory.append(web_memory)
        logger.info(f"Added web content to memory system (timestamp: {datetime.fromtimestamp(web_memory['timestamp']).isoformat()})")
        
        # Add app memory
        app_memory = {
            "type": "application",
            "application": "Chrome",
            "title": "Example Shopping Page - Chrome",
            "timestamp": time.time(),
            "source": "process_sensor"
        }
        
        # Add to memory
        memory_system.short_term_memory.append(app_memory)
        logger.info("Added Chrome application to memory system")
        
        logger.info("Memory items added successfully. The Memory Trigger Service should detect these items in its next cycle.")
        logger.info("If the frontend overlay is running, it should display notifications about the shopping content.")
        logger.info("Note: This test only adds memories but doesn't create the service - it relies on the existing running service.")
        
        return True
    
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        result = asyncio.run(main())
        if result:
            logger.info("✅ Test completed successfully")
        else:
            logger.error("❌ Test failed")
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
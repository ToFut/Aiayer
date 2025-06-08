#!/usr/bin/env python3
"""
Enable Context Memory Promotion

This script enables the promotion of contextual memory to long-term memory
by extending the existing memory system.
"""
import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/context_promotion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("context_promotion")

# Ensure path includes the current directory
sys.path.append('.')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
try:
    from memory.memory_system_extension import extend_memory_system
    from memory.memory_system import MemorySystem
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

async def main():
    """Main function to enable context memory promotion"""
    parser = argparse.ArgumentParser(description="Enable context memory promotion")
    parser.add_argument("--interval", type=int, default=300, 
                        help="Promotion interval in seconds (default: 300)")
    parser.add_argument("--threshold", type=float, default=0.6, 
                        help="Significance threshold (0.0-1.0, default: 0.6)")
    parser.add_argument("--manual", action="store_true", 
                        help="Run a single manual promotion and exit")
    parser.add_argument("--memory-id", type=str, 
                        help="Specific memory ID to promote (only with --manual)")
    args = parser.parse_args()
    
    logger.info(f"Starting context memory promotion utility with interval={args.interval}s, threshold={args.threshold}")
    
    # Get reference to the memory system
    try:
        memory_system = MemorySystem()
        logger.info("Successfully obtained reference to memory system")
    except Exception as e:
        logger.error(f"Failed to create memory system: {e}")
        sys.exit(1)
    
    # Create and initialize the extension
    try:
        # If using the factory method
        extension = extend_memory_system(memory_system)
        
        # Set custom parameters
        if extension.context_promotion:
            extension.context_promotion.promotion_interval = args.interval
            extension.context_promotion.significance_threshold = args.threshold
            logger.info(f"Updated promotion parameters: interval={args.interval}s, threshold={args.threshold}")
        
        # Wait for initialization to complete
        await asyncio.sleep(2)
        
        # Run manual promotion if requested
        if args.manual:
            logger.info("Running manual promotion")
            result = await extension.promote_context_to_long_term(args.memory_id)
            logger.info(f"Manual promotion result: {result}")
            
            # Exit after manual promotion
            return
        
        # Keep the script running to continue periodic promotion
        logger.info("Context memory promotion is now running. Press Ctrl+C to stop.")
        
        # Wait indefinitely for context promotion to run in the background
        while True:
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error in context memory promotion: {e}")
    finally:
        # Shutdown the extension
        if 'extension' in locals():
            await extension.shutdown()
        logger.info("Context memory promotion stopped")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs/memory', exist_ok=True)
    
    # Run the main function
    asyncio.run(main())
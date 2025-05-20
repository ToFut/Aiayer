#!/usr/bin/env python3
"""
Test Memory Logging
Tests the memory logging functionality for different types of memory.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.memory_system import MemorySystem
from memory.memory_logger import MemoryLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def test_memory_logging():
    """Test memory logging functionality."""
    try:
        # Initialize memory system
        memory_system = MemorySystem()
        logger.info("Memory system initialized")
        
        # Test data
        test_data = {
            'conscious': {
                'thought': 'This is a conscious thought',
                'timestamp': datetime.now().isoformat()
            },
            'short_term': {
                'message': 'This is a short-term memory',
                'timestamp': datetime.now().isoformat()
            },
            'long_term': {
                'fact': 'This is a long-term memory',
                'timestamp': datetime.now().isoformat()
            },
            'context': {
                'situation': 'This is a contextual memory',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Test adding to each memory type
        logger.info("Testing memory additions...")
        
        # Add to conscious memory
        memory_system._add_to_memory_storage(test_data['conscious'], 'conscious')
        logger.info("Added to conscious memory")
        
        # Add to short-term memory
        memory_system._add_to_memory_storage(test_data['short_term'], 'short_term')
        logger.info("Added to short-term memory")
        
        # Add to long-term memory
        memory_system._add_to_memory_storage(test_data['long_term'], 'long_term')
        logger.info("Added to long-term memory")
        
        # Add to context memory
        memory_system._add_to_memory_storage(test_data['context'], 'context')
        logger.info("Added to context memory")
        
        # Test saving memory state
        logger.info("Testing memory state saving...")
        memory_system._save_memory_state()
        
        # Test clearing memory
        logger.info("Testing memory clearing...")
        memory_system.clear()
        
        # Verify logs were created
        log_dir = 'logs/memory'
        log_files = os.listdir(log_dir)
        logger.info(f"Created log files: {log_files}")
        
        # Check content of each log file
        for log_file in log_files:
            if log_file.endswith('.log'):
                with open(os.path.join(log_dir, log_file), 'r') as f:
                    content = f.read()
                    logger.info(f"Content of {log_file}:\n{content[:500]}...")
        
        logger.info("Memory logging tests completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing memory logging: {e}")
        return False

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs/memory', exist_ok=True)
    
    # Run tests
    success = asyncio.run(test_memory_logging())
    sys.exit(0 if success else 1) 
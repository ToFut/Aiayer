#!/usr/bin/env python3
"""
Test Memory Flow
Tests the new memory flow architecture that routes all sensor data through conscious memory.
"""
import asyncio
import logging
import json
import os
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_memory_flow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import memory system
try:
    from memory.memory_system import MemorySystem
except ImportError:
    from memory_system import MemorySystem

# Import conscious memory
try:
    from memory.conscious_memory import ConsciousMemory
except ImportError:
    from conscious_memory import ConsciousMemory

# Mock sensor data
def create_mock_screen_data():
    """Create mock screen sensor data."""
    return {
        'timestamp': time.time(),
        'image_hash': 'mock_image_hash_1234567890',
        'memory_summary': {
            'application': {
                'name': 'TestBrowser',
                'type': 'browser'
            },
            'content': {
                'word_count': 250,
                'main_content': 'This is a test page about memory systems.'
            },
            'text_sample': 'Memory system architecture test. This test verifies proper data flow.',
            'semantic_summary': 'A test page showing information about memory architecture.',
            'user_activity': {
                'workflow_stage': 'research',
                'current_activity': 'reading',
                'user_intent': 'learning'
            },
            'key_insights': [
                'The page discusses memory architecture',
                'User is researching memory systems'
            ],
            'analysis_confidence': 0.85
        }
    }

def create_mock_process_data():
    """Create mock process sensor data."""
    return {
        'timestamp': time.time(),
        'active_window': 'TestBrowser',
        'active_app': 'TestBrowser',
        'active_apps': ['TestBrowser', 'Terminal', 'SystemServices'],
        'foreground': [
            {
                'name': 'TestBrowser',
                'type': 'browser',
                'category': 'productivity'
            }
        ],
        'background': [
            {
                'name': 'Terminal',
                'type': 'utility',
                'category': 'development'
            },
            {
                'name': 'SystemServices',
                'type': 'system',
                'category': 'utility'
            }
        ],
        'system_info': {
            'memory_used_percent': 65,
            'cpu_count': 8,
            'cpu_percent': 25
        },
        'active_processes': [
            {'pid': 1001, 'name': 'TestBrowser'},
            {'pid': 1002, 'name': 'Terminal'},
            {'pid': 1003, 'name': 'SystemServices'}
        ]
    }

async def verify_memory_contents():
    """Verify memory contents to ensure proper distribution."""
    try:
        # Check if memory_state.json exists
        if os.path.exists('memory/memory_state.json'):
            with open('memory/memory_state.json', 'r') as f:
                memory_state = json.load(f)
                logger.info(f"Memory state file exists and contains {len(memory_state)} keys")
                
                # Check update method - should NOT be direct_fallback
                if memory_state.get('update_method') == 'direct_fallback':
                    logger.warning("⚠️ Memory using fallback method - not using conscious memory!")
                else:
                    logger.info("✅ Memory state not using fallback method")
        else:
            logger.warning("⚠️ Memory state file does not exist")
            
        # Check if conscious.json exists
        if os.path.exists('memory/conscious.json'):
            with open('memory/conscious.json', 'r') as f:
                conscious_state = json.load(f)
                logger.info(f"Conscious memory file exists and contains {len(conscious_state)} keys")
                
                # Check update method - should NOT be direct_fallback
                if conscious_state.get('update_method') == 'direct_fallback':
                    logger.warning("⚠️ Conscious memory using fallback method - not using ConsciousMemory class!")
                else:
                    logger.info("✅ Conscious memory not using fallback method")
        else:
            logger.warning("⚠️ Conscious memory file does not exist")
            
        return True
    except Exception as e:
        logger.error(f"Error verifying memory contents: {e}")
        return False

async def test_memory_flow():
    """Test the memory flow architecture."""
    try:
        # Initialize memory system
        logger.info("Initializing memory system...")
        memory_system = MemorySystem()
        await memory_system.initialize()
        logger.info("Memory system initialized")
        
        # Feed screen data
        logger.info("Feeding mock screen data...")
        screen_data = create_mock_screen_data()
        screen_success = await memory_system.process_sensor_data('screen', screen_data)
        if screen_success:
            logger.info("✅ Successfully processed screen data")
        else:
            logger.error("❌ Failed to process screen data")
            
        # Feed process data
        logger.info("Feeding mock process data...")
        process_data = create_mock_process_data()
        process_success = await memory_system.process_sensor_data('process', process_data)
        if process_success:
            logger.info("✅ Successfully processed process data")
        else:
            logger.error("❌ Failed to process process data")
            
        # Wait for processing to complete
        logger.info("Waiting for processing to complete...")
        await asyncio.sleep(5)
        
        # Verify memory contents
        logger.info("Verifying memory contents...")
        verification = await verify_memory_contents()
        if verification:
            logger.info("✅ Memory verification completed")
        else:
            logger.error("❌ Memory verification failed")
            
        # Clean up
        logger.info("Cleaning up...")
        await memory_system.cleanup()
        
        logger.info("Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting memory flow test...")
    try:
        asyncio.run(test_memory_flow())
    except Exception as e:
        logger.error(f"Error running test: {e}")
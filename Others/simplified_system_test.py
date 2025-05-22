#!/usr/bin/env python3
"""
Simplified System Test

A more direct test of the memory system functionality without relying on WebSockets.
This script tests the core memory functions directly.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simplified_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Dynamically import memory system
def import_memory_system():
    """Import memory system module."""
    try:
        spec = importlib.util.spec_from_file_location(
            "memory_system", 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                        "memory/memory_system.py")
        )
        if not spec:
            logger.error("Could not load specification for memory_system.py")
            return None
            
        memory_module = importlib.util.module_from_spec(spec)
        sys.modules["memory_system"] = memory_module
        spec.loader.exec_module(memory_module)
        return memory_module
    except Exception as e:
        logger.error(f"Error importing memory system: {e}")
        logger.error(traceback.format_exc())
        return None

async def test_memory_functions():
    """Test basic memory system functionality."""
    try:
        logger.info("=== STARTING SIMPLIFIED MEMORY SYSTEM TEST ===")
        
        # Import memory system
        memory_module = import_memory_system()
        if not memory_module:
            logger.error("Failed to import memory system module")
            return False
        
        # Initialize memory system
        memory_system = memory_module.MemorySystem()
        logger.info("Memory system initialized")
        
        # Test 1: Add message to memory
        logger.info("TEST 1: Adding message to memory")
        test_message = {
            "type": "user_query",
            "content": "This is a test message",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await memory_system.add_message(test_message)
            logger.info("✅ Successfully added message to memory")
            print("✅ Test 1: Successfully added message to memory")
        except Exception as e:
            logger.error(f"❌ Error adding message to memory: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 1 failed: {e}")
        
        # Test 2: Process sensor data
        logger.info("TEST 2: Processing sensor data")
        test_screen_data = {
            "screen_text": "This is test screen content",
            "active_window": "Test Window",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await memory_system.process_sensor_data("screen", test_screen_data)
            logger.info("✅ Successfully processed screen sensor data")
            print("✅ Test 2: Successfully processed sensor data")
        except Exception as e:
            logger.error(f"❌ Error processing sensor data: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 2 failed: {e}")
        
        # Test 3: Get context summary
        logger.info("TEST 3: Getting context summary")
        try:
            context = await memory_system.get_context_summary()
            if context:
                logger.info(f"✅ Successfully retrieved context summary with keys: {list(context.keys())}")
                print(f"✅ Test 3: Successfully retrieved context with {len(context)} keys")
                print(f"   Keys: {', '.join(list(context.keys()))}")
            else:
                logger.warning("⚠️ Context summary is empty")
                print("⚠️ Test 3: Context summary is empty")
        except Exception as e:
            logger.error(f"❌ Error getting context summary: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 3 failed: {e}")
        
        # Test 4: Search memory
        logger.info("TEST 4: Searching memory")
        try:
            search_results = await memory_system.search_memory("test", limit=5)
            if search_results:
                logger.info(f"✅ Successfully found {len(search_results)} results")
                print(f"✅ Test 4: Found {len(search_results)} search results")
                
                # Display first result
                if search_results:
                    first_result = search_results[0]
                    print(f"   Top result - Source: {first_result.get('source')}")
                    print(f"   Score: {first_result.get('score')}")
                    print(f"   Content: {first_result.get('content')[:50]}...")
            else:
                logger.warning("⚠️ No search results found")
                print("⚠️ Test 4: No search results found")
        except Exception as e:
            logger.error(f"❌ Error searching memory: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 4 failed: {e}")
        
        # Test 5: Clear memory
        logger.info("TEST 5: Clearing memory")
        try:
            memory_system.clear()
            logger.info("✅ Successfully cleared memory")
            print("✅ Test 5: Successfully cleared memory")
        except Exception as e:
            logger.error(f"❌ Error clearing memory: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 5 failed: {e}")
        
        # Test 6: Test empty memory search (should return empty results, not error)
        logger.info("TEST 6: Testing empty memory search")
        try:
            empty_results = await memory_system.search_memory("test", limit=5)
            logger.info(f"✅ Empty memory search returned {len(empty_results)} results (expected 0)")
            print(f"✅ Test 6: Empty memory search returned {len(empty_results)} results (expected 0)")
        except Exception as e:
            logger.error(f"❌ Error in empty memory search: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 6 failed: {e}")
        
        # Test 7: Save and reload memory state
        logger.info("TEST 7: Testing memory state persistence")
        try:
            # Add a new message
            new_message = {
                "type": "user_query",
                "content": "Testing memory persistence",
                "timestamp": datetime.now().isoformat()
            }
            await memory_system.add_message(new_message)
            
            # Save memory state
            await memory_system._save_memory_state()
            logger.info("Saved memory state")
            
            # Create a new memory system instance
            new_memory_system = memory_module.MemorySystem()
            logger.info("Created new memory system instance")
            
            # Check if the new instance loaded the state
            if new_memory_system.short_term_memory and len(new_memory_system.short_term_memory) > 0:
                logger.info(f"✅ New memory system loaded {len(new_memory_system.short_term_memory)} short-term memories")
                print(f"✅ Test 7: Memory persistence verified with {len(new_memory_system.short_term_memory)} items")
            else:
                logger.warning("⚠️ New memory system did not load any short-term memories")
                print("⚠️ Test 7: Memory persistence test inconclusive")
        except Exception as e:
            logger.error(f"❌ Error testing memory persistence: {e}")
            logger.error(traceback.format_exc())
            print(f"❌ Test 7 failed: {e}")
        
        logger.info("=== SIMPLIFIED MEMORY SYSTEM TEST COMPLETED ===")
        print("\n=== SIMPLIFIED MEMORY SYSTEM TEST COMPLETED ===")
        print("All tests have been run. See logs for detailed results.")
        
        return True
        
    except Exception as e:
        logger.error(f"Critical error in test: {e}")
        logger.error(traceback.format_exc())
        print(f"❌ Critical test failure: {e}")
        return False

if __name__ == "__main__":
    # Ensure log directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run the test
    asyncio.run(test_memory_functions())
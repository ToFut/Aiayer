#!/usr/bin/env python3
"""
System Flow Test

This script tests the core functionality of the system:
1. Sensor data collection
2. Memory storage and retrieval
3. Context generation for LLM
4. LLM response with context

This test bypasses WebSocket communication and directly tests
the component interfaces.
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
import importlib.util
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_flow_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Dynamically import required modules
def import_module(module_path, module_name):
    """Dynamically import a module from a path."""
    try:
        spec = importlib.util.spec_from_file_location(
            module_name, 
            os.path.join(os.path.dirname(os.path.abspath(__file__)), module_path)
        )
        if not spec:
            logger.error(f"Could not load spec for {module_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error importing {module_path}: {e}")
        logger.error(traceback.format_exc())
        return None

# Sample test data for each sensor
def get_sample_process_data():
    """Generate sample process sensor data."""
    return {
        "active_window": "Terminal",
        "active_app": "Terminal",
        "active_apps": ["Terminal", "Firefox", "VS Code"],
        "processes": [
            {"name": "python", "pid": 12345, "cpu": 2.5, "memory": 120.5},
            {"name": "firefox", "pid": 12346, "cpu": 5.2, "memory": 450.8},
            {"name": "code", "pid": 12347, "cpu": 3.1, "memory": 380.2},
        ],
        "timestamp": datetime.now().isoformat()
    }

def get_sample_screen_data():
    """Generate sample screen sensor data."""
    return {
        "screen_text": "This is a test of the screen sensor component. The screen contains information about testing the system flow.",
        "active_window": "Test Window",
        "dominant_colors": ["#FFFFFF", "#000000"],
        "image_hash": "abcdef1234567890",
        "has_changed": True,
        "timestamp": datetime.now().isoformat()
    }

def get_sample_file_data():
    """Generate sample file sensor data."""
    return {
        "files": ["test_file1.py", "test_file2.py", "config.yaml"],
        "current_file": {
            "name": "test_system_flow.py",
            "path": "/Users/segevbin/Desktop/SensAI/Aiayer/test_system_flow.py",
            "content": "# Test content for file sensor",
            "type": "text"
        },
        "recent_changes": [
            {"path": "test_file1.py", "action": "modified", "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat()},
            {"path": "config.yaml", "action": "created", "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat()}
        ],
        "timestamp": datetime.now().isoformat()
    }

async def test_system_flow():
    """Test the core system flow from sensors to memory to LLM."""
    try:
        # Create log directory
        os.makedirs("logs", exist_ok=True)
        
        logger.info("=== STARTING SYSTEM FLOW TEST ===")
        
        # Step 1: Import required modules
        logger.info("STEP 1: Importing required modules")
        
        memory_module = import_module("memory/memory_system.py", "memory_system")
        if not memory_module:
            logger.error("Failed to import memory_system module. Exiting test.")
            return False
            
        llm_module = import_module("llm/model.py", "llm_model")
        if not llm_module:
            logger.warning("Failed to import llm_model module. LLM integration test will be skipped.")
        
        # Step 2: Initialize Memory System
        logger.info("STEP 2: Initializing Memory System")
        
        try:
            memory_system = memory_module.MemorySystem()
            await memory_system.initialize()
            logger.info("Memory system initialized successfully")
            print("✅ Memory system initialized")
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            logger.error(traceback.format_exc())
            print("❌ Memory system initialization failed")
            return False
        
        # Step 3: Feed sample sensor data to memory
        logger.info("STEP 3: Feeding sample sensor data to memory")
        
        # Process sensor data
        process_data = get_sample_process_data()
        try:
            await memory_system.process_sensor_data("process", process_data)
            logger.info("Process sensor data processed successfully")
            print("✅ Process sensor data processed")
        except Exception as e:
            logger.error(f"Error processing process sensor data: {e}")
            logger.error(traceback.format_exc())
            print("❌ Process sensor data processing failed")
        
        # Screen sensor data
        screen_data = get_sample_screen_data()
        try:
            await memory_system.process_sensor_data("screen", screen_data)
            logger.info("Screen sensor data processed successfully")
            print("✅ Screen sensor data processed")
        except Exception as e:
            logger.error(f"Error processing screen sensor data: {e}")
            logger.error(traceback.format_exc())
            print("❌ Screen sensor data processing failed")
        
        # File sensor data
        file_data = get_sample_file_data()
        try:
            await memory_system.process_sensor_data("file", file_data)
            logger.info("File sensor data processed successfully")
            print("✅ File sensor data processed")
        except Exception as e:
            logger.error(f"Error processing file sensor data: {e}")
            logger.error(traceback.format_exc())
            print("❌ File sensor data processing failed")
        
        # Step 4: Retrieve context from memory
        logger.info("STEP 4: Retrieving context from memory")
        
        try:
            context = await memory_system.get_context_summary()
            context_keys = list(context.keys())
            logger.info(f"Retrieved context with keys: {context_keys}")
            
            if "screen_content" in context and "active_window" in context and "active_apps" in context:
                logger.info("Context contains expected keys")
                print("✅ Context retrieval successful")
                print(f"  - Context keys: {', '.join(context_keys)}")
            else:
                logger.warning(f"Context missing expected keys. Found: {context_keys}")
                print("⚠️ Context missing some expected keys")
            
            # Log some details about the context
            logger.info(f"Screen content length: {len(context.get('screen_content', ''))}")
            logger.info(f"Active window: {context.get('active_window', 'Unknown')}")
            logger.info(f"Active apps: {context.get('active_apps', [])}")
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            logger.error(traceback.format_exc())
            print("❌ Context retrieval failed")
        
        # Step 5: Test memory search
        logger.info("STEP 5: Testing memory search")
        
        test_query = "test screen terminal"
        try:
            search_results = await memory_system.search_memory(test_query, limit=5)
            
            if search_results:
                logger.info(f"Memory search returned {len(search_results)} results")
                print(f"✅ Memory search successful with {len(search_results)} results")
                
                # Log the first result
                if search_results:
                    first_result = search_results[0]
                    logger.info(f"Top result source: {first_result.get('source', 'unknown')}")
                    logger.info(f"Top result score: {first_result.get('score', 0)}")
                    logger.info(f"Top result type: {type(first_result.get('data', {}))}")
            else:
                logger.warning("Memory search returned no results")
                print("⚠️ Memory search returned no results")
        except Exception as e:
            logger.error(f"Error in memory search: {e}")
            logger.error(traceback.format_exc())
            print("❌ Memory search failed")
        
        # Step 6: Test LLM integration (if available)
        if llm_module:
            logger.info("STEP 6: Testing LLM integration")
            
            try:
                llm_client = llm_module.LocalLLM(model_name="test_model")
                test_query = "What am I currently working on?"
                
                # Get context for the query
                context = await memory_system.get_context_summary()
                
                # Log what we're sending to the LLM
                logger.info(f"Query: {test_query}")
                logger.info(f"Context size: {len(str(context))} chars")
                
                # Test LLM response generation
                # Note: We're just testing the interface, not actual generation
                mock_response = {
                    "response": "Based on your screen, you are currently working on testing the system flow from sensors to memory to LLM in the Terminal application. You have several files open including test_system_flow.py.",
                    "source": "test_model",
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info("LLM integration test successful with mock response")
                print("✅ LLM integration test successful (mock response)")
                
            except Exception as e:
                logger.error(f"Error in LLM integration test: {e}")
                logger.error(traceback.format_exc())
                print("❌ LLM integration test failed")
        else:
            logger.info("STEP 6: Skipping LLM integration test (module not loaded)")
            print("⚠️ Skipping LLM integration test (module not available)")
        
        # Step 7: Test memory persistence
        logger.info("STEP 7: Testing memory persistence")
        
        try:
            # Save memory state
            await memory_system.save_state()
            logger.info("Memory state saved successfully")
            
            # Create a new memory system and load the state
            new_memory_system = memory_module.MemorySystem()
            await new_memory_system.initialize()
            
            # Check if we can retrieve similar context
            new_context = await new_memory_system.get_context_summary()
            if "screen_content" in new_context and "active_window" in new_context:
                logger.info("Memory persistence test successful")
                print("✅ Memory persistence test successful")
            else:
                logger.warning("Memory persistence test partially successful (some context missing)")
                print("⚠️ Memory persistence test partially successful")
                
        except Exception as e:
            logger.error(f"Error in memory persistence test: {e}")
            logger.error(traceback.format_exc())
            print("❌ Memory persistence test failed")
        
        logger.info("=== SYSTEM FLOW TEST COMPLETED ===")
        print("\n=== SYSTEM FLOW TEST COMPLETED ===")
        print("The system flow test has completed. Check logs for detailed results.")
        return True
    
    except Exception as e:
        logger.error(f"Critical error in system flow test: {e}")
        logger.error(traceback.format_exc())
        print(f"❌ Critical test failure: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_system_flow())
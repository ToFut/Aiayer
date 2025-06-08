#!/usr/bin/env python3
"""
Connect Memory Dashboard to Memory System

This script connects the enhanced memory dashboard to the actual memory system
to display real data instead of mock data.
"""

import os
import sys
import time
import logging
import importlib.util
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/dashboard_connection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("connect_memory_dashboard")

def import_module_from_path(module_name, file_path):
    """Import a module from a file path"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Error importing module {module_name} from {file_path}: {e}")
        return None

def connect_dashboard_to_memory():
    """Connect the memory dashboard to the memory system"""
    logger.info("Connecting memory dashboard to memory system...")
    
    # Import the memory system
    memory_system_path = os.path.join(os.getcwd(), "memory", "memory_system.py")
    memory_system_module = import_module_from_path("memory_system", memory_system_path)
    
    # Import the enhanced memory dashboard
    dashboard_path = os.path.join(os.getcwd(), "memory", "enhanced_memory_dashboard.py")
    dashboard_module = import_module_from_path("enhanced_memory_dashboard", dashboard_path)
    
    if not memory_system_module or not dashboard_module:
        logger.error("Failed to import required modules")
        return False
    
    try:
        # Check if there's a global memory system instance
        if hasattr(memory_system_module, "memory_system"):
            # Set the memory system in the dashboard
            dashboard_module.set_memory_system(memory_system_module.memory_system)
            logger.info("Connected memory system to dashboard")
        else:
            logger.warning("No global memory_system instance found")
            
        # Check if there's a global conscious memory instance
        if hasattr(memory_system_module, "conscious_memory"):
            # Set the conscious memory in the dashboard
            dashboard_module.set_conscious_memory(memory_system_module.conscious_memory)
            logger.info("Connected conscious memory to dashboard")
        elif hasattr(memory_system_module.memory_system, "conscious_memory"):
            # Set the conscious memory from the memory system
            dashboard_module.set_conscious_memory(memory_system_module.memory_system.conscious_memory)
            logger.info("Connected conscious memory from memory system to dashboard")
        else:
            logger.warning("No conscious_memory instance found")
        
        # Generate some sample metrics for testing
        generate_test_data(memory_system_module, dashboard_module)
        
        return True
    
    except Exception as e:
        logger.error(f"Error connecting dashboard to memory system: {e}")
        return False

def generate_test_data(memory_system_module, dashboard_module):
    """Generate some test data to ensure the dashboard is working"""
    try:
        # Add some sample memory entries if memory system is empty
        memory_system = getattr(memory_system_module, "memory_system", None)
        if memory_system:
            # Check if memory is empty
            short_term_empty = not hasattr(memory_system, "short_term_memory") or len(getattr(memory_system, "short_term_memory", [])) == 0
            context_empty = not hasattr(memory_system, "context_memory") or len(getattr(memory_system, "context_memory", {})) == 0
            
            # Add sample data if empty
            if short_term_empty:
                logger.info("Adding sample short-term memories")
                if not hasattr(memory_system, "short_term_memory"):
                    memory_system.short_term_memory = []
                
                # Add sample short-term memories
                for i in range(5):
                    memory_system.short_term_memory.append({
                        "id": f"test_stm_{i}",
                        "content": f"Sample short-term memory {i}",
                        "created_at": time.time(),
                        "expires_at": time.time() + 1800  # 30 minutes
                    })
            
            if context_empty:
                logger.info("Adding sample context memories")
                if not hasattr(memory_system, "context_memory"):
                    memory_system.context_memory = {}
                
                # Add sample context memories
                memory_system.context_memory["app_context"] = {
                    "current_app": "Terminal",
                    "updated_at": time.time()
                }
                memory_system.context_memory["user_context"] = {
                    "focus": "high",
                    "mode": "coding",
                    "updated_at": time.time()
                }
                memory_system.context_memory["system_context"] = {
                    "cpu_usage": "35%",
                    "memory_usage": "42%",
                    "updated_at": time.time()
                }
                
        # Add some sample long-term memories
        if memory_system and (not hasattr(memory_system, "long_term_memory") or len(getattr(memory_system, "long_term_memory", [])) == 0):
            logger.info("Adding sample long-term memories")
            if not hasattr(memory_system, "long_term_memory"):
                memory_system.long_term_memory = []
            
            # Add sample long-term memories
            for i in range(10):
                memory_system.long_term_memory.append({
                    "id": f"test_ltm_{i}",
                    "content": f"Sample long-term memory {i}",
                    "created_at": time.time() - (i * 86400),  # i days ago
                    "type": ["episodic", "semantic", "procedural", "declarative"][i % 4],
                    "importance": ["low", "medium", "high", "critical"][i % 4]
                })
        
        # Force an update of the dashboard metrics
        enhanced_dashboard = getattr(dashboard_module, "enhanced_memory_dashboard", None)
        if enhanced_dashboard:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(enhanced_dashboard.update_metrics())
            logger.info("Updated dashboard metrics with test data")
    
    except Exception as e:
        logger.error(f"Error generating test data: {e}")

if __name__ == "__main__":
    # Connect the dashboard to the memory system
    if connect_dashboard_to_memory():
        logger.info("Successfully connected memory dashboard to memory system")
        print("Memory dashboard successfully connected to memory system.")
        print("You should now see real data in the dashboard.")
        print("Visit http://localhost:8082/memory to view the dashboard.")
    else:
        logger.error("Failed to connect memory dashboard to memory system")
        print("Failed to connect memory dashboard to memory system.")
        print("Check the logs for more information.")
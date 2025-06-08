#!/usr/bin/env python3
"""
Test script to verify that fixed_universal_automation_handler can be imported properly
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("import_test")

def test_import():
    """Test importing the fixed_universal_automation_handler module"""
    try:
        logger.info("Current working directory: %s", os.getcwd())
        logger.info("Python path: %s", sys.path)
        
        logger.info("Attempting to import fixed_universal_automation_handler...")
        from fixed_universal_automation_handler import fixed_handle_universal_automation
        logger.info("✅ Successfully imported fixed_handle_universal_automation")
        return True
    except ImportError as e:
        logger.error("❌ ImportError: %s", str(e))
        
        # Try with absolute path
        try:
            logger.info("Attempting import with absolute path...")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(script_dir)
            logger.info("Added script directory to sys.path: %s", script_dir)
            logger.info("Updated Python path: %s", sys.path)
            
            from fixed_universal_automation_handler import fixed_handle_universal_automation
            logger.info("✅ Successfully imported fixed_handle_universal_automation with absolute path")
            return True
        except ImportError as e2:
            logger.error("❌ ImportError with absolute path: %s", str(e2))
            return False

if __name__ == "__main__":
    success = test_import()
    print("Import test result:", "SUCCESS" if success else "FAILED")
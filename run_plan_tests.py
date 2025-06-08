#!/usr/bin/env python3
"""
Test runner for plan persistence and automation handling system
"""

import os
import sys
import pytest
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """Set up the test environment"""
    # Create test directories
    os.makedirs("cache/plans", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Set up test log file
    log_file = f"logs/plan_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    logger.info("Test environment set up successfully")

def cleanup_test_environment():
    """Clean up the test environment"""
    try:
        # Clean up test plans
        if os.path.exists("cache/plans"):
            for file in os.listdir("cache/plans"):
                if file.endswith(".json"):
                    os.remove(os.path.join("cache/plans", file))
        logger.info("Test environment cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")

def run_tests():
    """Run the test suite"""
    try:
        # Set up environment
        setup_test_environment()
        
        # Run tests with pytest-asyncio
        logger.info("Starting test suite...")
        result = pytest.main([
            "-v",
            "--asyncio-mode=strict",
            "test_plan_persistence.py"
        ])
        
        # Check results
        if result == 0:
            logger.info("✅ All tests passed successfully!")
        else:
            logger.error("❌ Some tests failed!")
        
        return result
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return 1
        
    finally:
        # Clean up
        cleanup_test_environment()

if __name__ == "__main__":
    # Run tests
    exit_code = run_tests()
    sys.exit(exit_code) 
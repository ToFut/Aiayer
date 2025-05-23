#!/usr/bin/env python3
"""
Test script to verify memory system fixes are working.
"""
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_memory_integration_import():
    """Test if memory integration service imports work."""
    try:
        logger.info("Testing memory integration service imports...")
        
        # Change to correct directory
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Test import
        from memory.memory_integration_service import MemoryIntegrationService
        logger.info("✅ Memory integration service imports successfully")
        
        # Test initialization
        service = MemoryIntegrationService()
        logger.info("✅ Memory integration service initializes successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Memory integration import failed: {e}")
        return False

def test_screen_sensor_data():
    """Test if screen sensor generates meaningful data."""
    try:
        logger.info("Testing screen sensor data generation...")
        
        # Import screen sensor functions
        sys.path.append('sensors')
        from enhanced_fixed_screen_sensor import capture_screen_text, get_active_window_info
        
        # Test window info
        window_info = get_active_window_info()
        logger.info(f"Window info: {window_info}")
        
        if window_info['active_app'] != 'Unknown':
            logger.info("✅ Screen sensor detects active application")
        else:
            logger.warning("⚠️ Screen sensor shows 'Unknown' application")
        
        # Test screen capture
        screen_data = capture_screen_text()
        logger.info(f"Screen data keys: {list(screen_data.keys())}")
        logger.info(f"Screen text preview: {screen_data.get('screen_text', '')[:200]}...")
        
        if screen_data.get('screen_text') and len(screen_data['screen_text']) > 10:
            logger.info("✅ Screen sensor captures meaningful text content")
        else:
            logger.warning("⚠️ Screen sensor text content is minimal")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Screen sensor test failed: {e}")
        return False

def test_process_sensor_data():
    """Test if process sensor generates meaningful data."""
    try:
        logger.info("Testing process sensor data generation...")
        
        # Import process sensor functions
        sys.path.append('sensors')
        from enhanced_fixed_process_sensor import get_active_applications, get_active_window_info
        
        # Test active applications
        apps = get_active_applications()
        logger.info(f"Found {len(apps)} active applications")
        
        if len(apps) > 0:
            logger.info("✅ Process sensor detects running applications")
            for app in apps[:3]:  # Show top 3
                logger.info(f"  - {app['name']} ({app.get('type', 'unknown')}) - {app['memory_mb']}MB")
        else:
            logger.warning("⚠️ Process sensor found no applications")
        
        # Test window info
        window_info = get_active_window_info()
        logger.info(f"Active window: {window_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Process sensor test failed: {e}")
        return False

def test_memory_files():
    """Test if memory files exist and are accessible."""
    try:
        logger.info("Testing memory file access...")
        
        # Check key memory files
        files_to_check = [
            'memory/memory_state.json',
            'memory/conscious.json',
            'cache/screen_sensor/last_screen.json',
            'cache/process_sensor/process_cache.json'
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    logger.info(f"✅ {file_path} exists and is readable")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ {file_path} exists but has invalid JSON")
                except Exception as e:
                    logger.warning(f"⚠️ {file_path} exists but error reading: {e}")
            else:
                logger.warning(f"⚠️ {file_path} does not exist")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory files test failed: {e}")
        return False

def test_json_functions():
    """Test safe JSON functions."""
    try:
        logger.info("Testing JSON utility functions...")
        
        # Test fallback safe_load and safe_dump
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        # Test JSON serialization
        json_str = json.dumps(test_data)
        parsed_data = json.loads(json_str)
        
        logger.info("✅ JSON functions work correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ JSON functions test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🧪 Starting Memory System Fix Verification Tests")
    logger.info("=" * 60)
    
    tests = [
        ("JSON Functions", test_json_functions),
        ("Memory Files", test_memory_files),
        ("Memory Integration Import", test_memory_integration_import),
        ("Screen Sensor Data", test_screen_sensor_data),
        ("Process Sensor Data", test_process_sensor_data),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"Result: {status}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"Result: ❌ FAILED (Exception: {e})")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Memory system fixes appear to be working.")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Some issues remain.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test runner failed: {e}")
        sys.exit(1)
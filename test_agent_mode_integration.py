#!/usr/bin/env python3
"""
Test Agent Mode Integration
Verifies that the professional agent system is properly integrated with the backend
"""

import asyncio
import json
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_professional_agent_import():
    """Test that professional agent system can be imported"""
    try:
        from professional_agent_system import start_professional_agent_session, handle_agent_confirmation
        logger.info("✅ Professional agent system imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import professional agent system: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error importing professional agent system: {e}")
        return False

async def test_agent_session_creation():
    """Test creating an agent session"""
    try:
        from professional_agent_system import start_professional_agent_session
        
        # Test simple task
        result = await start_professional_agent_session("Click on Documents folder")
        
        if "error" in result:
            logger.error(f"❌ Agent session creation failed: {result['error']}")
            return False
        
        if "session_id" in result:
            logger.info(f"✅ Agent session created successfully: {result['session_id']}")
            return True
        
        logger.warning("⚠️ Agent session created but no session_id returned")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error creating agent session: {e}")
        return False

async def test_backend_integration():
    """Test backend integration with professional agent"""
    try:
        from enterprise_backend_8767 import EnterpriseBackend8767
        
        backend = EnterpriseBackend8767()
        
        # Test agent mode processing
        result = await backend.process_agent_mode("Click on Documents folder", "test_session")
        
        if "Error" in result:
            logger.error(f"❌ Backend agent mode failed: {result}")
            return False
        
        logger.info(f"✅ Backend agent mode integration working: {result}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backend integration test failed: {e}")
        return False

async def test_agent_request_handling():
    """Test agent request message handling"""
    try:
        from enterprise_backend_8767 import EnterpriseBackend8767
        
        backend = EnterpriseBackend8767()
        
        # Test agent request
        test_data = {
            "message": "Click on Documents folder to open file browser"
        }
        
        result = await backend.handle_agent_request(test_data, "test_client")
        
        if not result.get("success", False):
            logger.error(f"❌ Agent request handling failed: {result}")
            return False
        
        logger.info(f"✅ Agent request handling working: {result.get('type', 'unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Agent request test failed: {e}")
        return False

async def run_all_tests():
    """Run all integration tests"""
    logger.info("🧪 Starting Agent Mode Integration Tests")
    
    tests = [
        ("Professional Agent Import", test_professional_agent_import),
        ("Agent Session Creation", test_agent_session_creation),
        ("Backend Integration", test_backend_integration),
        ("Agent Request Handling", test_agent_request_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ FAILED: {test_name} - {e}")
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {status}: {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Agent mode integration is working correctly.")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Agent mode may have issues.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())
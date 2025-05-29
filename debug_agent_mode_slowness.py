#!/usr/bin/env python3
"""
Debug Agent Mode Slowness
Identify exactly where the delay is happening in agent mode processing
"""

import asyncio
import time
import logging
import sys
import json

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_agent_mode_steps():
    """Debug each step of agent mode processing"""
    logger.info("🔍 DEBUGGING AGENT MODE SLOWNESS")
    logger.info("="*60)
    
    total_start = time.time()
    
    # Step 1: Import backend
    step_start = time.time()
    try:
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        step_time = time.time() - step_start
        logger.info(f"✅ Step 1 - Backend import: {step_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Step 1 - Backend import failed: {e}")
        return
    
    # Step 2: Initialize backend
    step_start = time.time()
    try:
        backend = ContextualAIBackend()
        step_time = time.time() - step_start
        logger.info(f"✅ Step 2 - Backend initialization: {step_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Step 2 - Backend initialization failed: {e}")
        return
    
    # Step 3: Check fast automation availability
    step_start = time.time()
    try:
        # Check if fast automation is available in backend
        fast_available = False
        try:
            import enhanced_enterprise_backend_with_context as backend_module
            fast_available = getattr(backend_module, 'FAST_AUTOMATION_AVAILABLE', False)
            logger.info(f"🔧 FAST_AUTOMATION_AVAILABLE: {fast_available}")
        except:
            pass
        
        # Check global scope
        fast_in_globals = 'FAST_AUTOMATION_AVAILABLE' in globals()
        logger.info(f"🔧 FAST_AUTOMATION_AVAILABLE in globals: {fast_in_globals}")
        
        step_time = time.time() - step_start
        logger.info(f"✅ Step 3 - Fast automation check: {step_time:.2f}s")
    except Exception as e:
        logger.error(f"❌ Step 3 - Fast automation check failed: {e}")
    
    # Step 4: Memory system operations
    step_start = time.time()
    try:
        from memory.semantic_search_agent import add_memory, get_context_for_query
        
        # Test memory add
        await add_memory(
            "Debug test message in agent mode",
            source="debug_test",
            tags={"debug", "agent_mode", "test"}
        )
        
        # Test context retrieval
        context = await get_context_for_query("debug test message", max_context_length=500)
        
        step_time = time.time() - step_start
        logger.info(f"✅ Step 4 - Memory operations: {step_time:.2f}s")
        logger.info(f"📊 Context results: {len(context.get('relevant_memories', []))} memories")
    except Exception as e:
        logger.error(f"❌ Step 4 - Memory operations failed: {e}")
    
    # Step 5: Fast automation handler direct test
    step_start = time.time()
    try:
        from fast_universal_automation_handler import fast_universal_automation_handler
        
        plan_result = await fast_universal_automation_handler.create_universal_automation_plan(
            "search flight from nyc to miami", "debug_session"
        )
        
        step_time = time.time() - step_start
        logger.info(f"✅ Step 5 - Fast automation direct: {step_time:.2f}s")
        logger.info(f"📋 Plan success: {plan_result.get('success', False)}")
    except Exception as e:
        logger.error(f"❌ Step 5 - Fast automation direct failed: {e}")
    
    # Step 6: Simulate actual agent mode flow
    step_start = time.time()
    try:
        # Simulate the exact flow that happens in agent mode
        test_data = {
            "type": "chat_request",
            "mode": "Agent",
            "message": "search flight from nyc to miami",
            "session_id": "debug_test_session"
        }
        
        # This is the actual method that gets called
        response = await backend.handle_contextual_chat_request(test_data, "debug_client")
        
        step_time = time.time() - step_start
        logger.info(f"✅ Step 6 - Full agent mode flow: {step_time:.2f}s")
        logger.info(f"📤 Response success: {response.get('success', False)}")
        logger.info(f"📝 Response preview: {str(response.get('response', ''))[:100]}...")
    except Exception as e:
        logger.error(f"❌ Step 6 - Full agent mode flow failed: {e}")
    
    total_time = time.time() - total_start
    logger.info("="*60)
    logger.info(f"🏁 TOTAL DEBUG TIME: {total_time:.2f}s")
    logger.info("="*60)

async def debug_memory_performance():
    """Debug memory system performance specifically"""
    logger.info("\n🧠 DEBUGGING MEMORY SYSTEM PERFORMANCE")
    logger.info("-"*50)
    
    try:
        from memory.semantic_search_agent import add_memory, get_context_for_query
        
        # Test memory add performance
        start = time.time()
        for i in range(5):
            await add_memory(f"Test memory {i}", source="perf_test", tags={"test"})
        add_time = time.time() - start
        logger.info(f"📝 Adding 5 memories: {add_time:.2f}s ({add_time/5:.3f}s each)")
        
        # Test context retrieval performance
        start = time.time()
        context = await get_context_for_query("test search query", max_context_length=500)
        search_time = time.time() - start
        logger.info(f"🔍 Context search: {search_time:.2f}s")
        logger.info(f"📊 Results: {len(context.get('relevant_memories', []))} memories")
        
        # Test multiple searches
        start = time.time()
        for i in range(3):
            await get_context_for_query(f"test query {i}", max_context_length=200)
        multi_search_time = time.time() - start
        logger.info(f"🔍 3 searches: {multi_search_time:.2f}s ({multi_search_time/3:.3f}s each)")
        
    except Exception as e:
        logger.error(f"❌ Memory performance test failed: {e}")

async def debug_backend_globals():
    """Debug the globals issue that might be causing fast automation not to be used"""
    logger.info("\n🌐 DEBUGGING GLOBALS AND FAST AUTOMATION")
    logger.info("-"*50)
    
    try:
        # Check different ways to access FAST_AUTOMATION_AVAILABLE
        import enhanced_enterprise_backend_with_context as backend_module
        
        # Method 1: Module attribute
        fast_attr = getattr(backend_module, 'FAST_AUTOMATION_AVAILABLE', None)
        logger.info(f"🔧 Module attribute: {fast_attr}")
        
        # Method 2: Check globals in module
        module_globals = getattr(backend_module, '__dict__', {})
        fast_in_module = 'FAST_AUTOMATION_AVAILABLE' in module_globals
        logger.info(f"🔧 In module dict: {fast_in_module}")
        
        # Method 3: Check current globals
        fast_in_current = 'FAST_AUTOMATION_AVAILABLE' in globals()
        logger.info(f"🔧 In current globals: {fast_in_current}")
        
        # Method 4: Try to import and check
        try:
            from enhanced_enterprise_backend_with_context import FAST_AUTOMATION_AVAILABLE
            logger.info(f"🔧 Direct import: {FAST_AUTOMATION_AVAILABLE}")
        except ImportError:
            logger.warning("🔧 Cannot import FAST_AUTOMATION_AVAILABLE directly")
        
        # Check what happens in the exact condition used in backend
        condition_result = 'FAST_AUTOMATION_AVAILABLE' in globals() and globals().get('FAST_AUTOMATION_AVAILABLE', False)
        logger.info(f"🔧 Backend condition result: {condition_result}")
        
    except Exception as e:
        logger.error(f"❌ Globals debug failed: {e}")

async def main():
    """Run all debugging tests"""
    await debug_agent_mode_steps()
    await debug_memory_performance()
    await debug_backend_globals()
    
    logger.info("\n🎯 DIAGNOSIS RECOMMENDATIONS:")
    logger.info("1. Check which step takes longest")
    logger.info("2. Verify fast automation is being used")
    logger.info("3. Check memory system performance")
    logger.info("4. Verify globals accessibility")

if __name__ == "__main__":
    asyncio.run(main())
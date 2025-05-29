#!/usr/bin/env python3
"""
Quick Agent Mode Test
Fast test to see exactly what happens in agent mode
"""

import asyncio
import logging

# Setup detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_agent_test():
    """Quick test of agent mode to see logs"""
    try:
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        # Check variables first
        import enhanced_enterprise_backend_with_context as backend_module
        fast_available = getattr(backend_module, 'FAST_AUTOMATION_AVAILABLE', False)
        logger.info(f"🔧 FAST_AUTOMATION_AVAILABLE: {fast_available}")
        
        backend = ContextualAIBackend()
        logger.info(f"🔧 Backend automation_handler: {backend.automation_handler}")
        
        # Test the exact method that gets called
        test_data = {
            "mode": "Agent",
            "message": "search flight from nyc to miami",
            "session_id": "quick_test"
        }
        
        logger.info("🎯 Starting agent mode test...")
        
        # Call the non-streaming version for simpler debugging
        result = await backend.handle_contextual_chat_request(test_data, "test_client")
        
        logger.info(f"✅ Result success: {result.get('success', False)}")
        response_text = str(result.get('response', ''))
        logger.info(f"📝 Response preview: {response_text[:200]}...")
        
        # Check if it's an automation response
        if 'AUTOMATION' in response_text and 'PLAN' in response_text:
            logger.info("🎯 SUCCESS: Automation plan generated!")
        else:
            logger.info("⚠️ Issue: Using LLM fallback instead of automation")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(quick_agent_test())
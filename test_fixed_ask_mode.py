#!/usr/bin/env python3
"""
Test the fixed ASK mode with brain router to see if it now uses semantic search
"""

import asyncio
import json
import logging
import sys
import os

# Add path for brain router
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ask_mode():
    """Test ASK mode with the fixed brain router"""
    try:
        # Import brain router
        from brain.core.brain_router import process_chat_request
        
        print("🧠 Testing Fixed ASK Mode with Brain Router")
        print("=" * 50)
        
        # Test the specific query about running apps
        test_queries = [
            "what apps are running on my PC?",
            "what applications do I have open?", 
            "show me what's currently running",
            "what software is active on my computer?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("-" * 30)
            
            # Call ASK mode
            result = await process_chat_request(
                mode="Ask",
                query=query,
                user_id="test_user",
                session_id="test_session"
            )
            
            print(f"✅ Success: {result['success']}")
            print(f"🎯 Mode: {result['mode']}")
            print(f"⏱️  Processing Time: {result['processing_time']:.2f}s")
            print(f"🔧 Resources Used: {result['resources_used']}")
            print(f"📊 Confidence: {result['confidence']:.2f}")
            print(f"✔️  Verification: {result['verification_status']}")
            
            print(f"\n📝 Response:")
            print(result['response'])
            
            if result.get('metadata'):
                print(f"\n🔍 Metadata:")
                for key, value in result['metadata'].items():
                    print(f"  {key}: {value}")
            
            print("\n" + "="*50)
        
        # Test system status
        print("\n🔍 Testing Brain Router System Status")
        from brain.core.brain_router import brain_router
        status = brain_router.get_system_status()
        print(json.dumps(status, indent=2))
        
    except Exception as e:
        print(f"❌ Error testing ASK mode: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ask_mode())
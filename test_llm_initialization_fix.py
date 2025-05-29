#!/usr/bin/env python3
"""
Test LLM initialization fix for Universal Automation Handler
"""

import asyncio
import sys
import os
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from universal_intelligent_automation_handler import universal_automation_handler

async def test_llm_initialization():
    """Test if LLM service can be properly initialized"""
    
    print("🧪 Testing LLM Initialization Fix")
    print("=" * 60)
    
    # Test LLM initialization
    print("\n🔧 Testing LLM Service Initialization:")
    print("-" * 40)
    
    try:
        # Ensure LLM service initialization
        await universal_automation_handler._ensure_llm_service()
        
        print(f"LLM Initialized: {universal_automation_handler.llm_initialized}")
        print(f"LLM Service Available: {universal_automation_handler.llm_service is not None}")
        
        if universal_automation_handler.llm_service:
            print("✅ LLM service successfully initialized!")
        else:
            print("❌ LLM service failed to initialize")
            
    except Exception as e:
        print(f"❌ Error during LLM initialization: {e}")
    
    # Test actual plan creation
    print("\n🤖 Testing Plan Creation:")
    print("-" * 40)
    
    test_requests = [
        "search for Python tutorials on Google",
        "open Calculator and compute 15 * 27", 
        "find flights from NYC to Miami"
    ]
    
    for request in test_requests:
        print(f"\nTesting: '{request}'")
        
        try:
            start_time = time.time()
            result = await universal_automation_handler.create_universal_automation_plan(
                request, "test_session"
            )
            processing_time = time.time() - start_time
            
            print(f"Success: {result['success']}")
            print(f"Processing Time: {processing_time:.2f}s")
            
            if result['success']:
                print("✅ Real LLM plan created!")
                print(f"Plan ID: {result.get('plan_id', 'none')}")
                print(f"Request Type: {result.get('request_type', 'unknown')}")
                print(f"Universal Planning: {result.get('universal_planning', False)}")
                
                # Show first 200 chars of response
                response_preview = result.get('response', '')[:200]
                if len(result.get('response', '')) > 200:
                    response_preview += "..."
                print(f"Response Preview: {response_preview}")
            else:
                print("❌ Plan creation failed")
                print(f"Error: {result.get('response', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception during plan creation: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_llm_initialization())
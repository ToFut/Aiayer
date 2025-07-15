#!/usr/bin/env python3
"""
Test LLM Performance and Debug Slow Response Issue
"""

import asyncio
import time
import json
from llm_plan_creator import LLMPlanCreator

async def test_llm_performance():
    """Test LLM performance and debug slow responses"""
    print("🧪 Testing LLM Performance...")
    
    creator = LLMPlanCreator()
    
    test_cases = [
        "Search Segev in Google",
        "Open Calculator",
        "Click on the center of the screen"
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: '{test_case}'")
        
        # Test 1: Direct LLM call
        print("🔍 Testing direct LLM call...")
        t0 = time.time()
        try:
            from llm.llm_service import LLMService
            llm_service = LLMService()
            
            # Test simple prompt
            simple_prompt = "What is 2+2?"
            messages = [{"role": "user", "content": simple_prompt}]
            
            response = await llm_service.llm_client.generate_response(messages)
            t1 = time.time()
            print(f"⏱️ Simple LLM call time: {t1-t0:.2f}s")
            print(f"📄 Response: {response[:100]}...")
            
        except Exception as e:
            print(f"❌ LLM service error: {e}")
        
        # Test 2: Plan creator
        print("🔍 Testing plan creator...")
        t0 = time.time()
        try:
            result = await creator.create_llm_plan(test_case, "test_session")
            t1 = time.time()
            print(f"⏱️ Plan creator time: {t1-t0:.2f}s")
            print(f"✅ Success: {result.get('success', False)}")
            
            if result.get('success') and result.get('plan'):
                plan = result['plan']
                steps = plan.get('steps', [])
                print(f"📋 Plan: {plan.get('title', 'No title')}")
                print(f"🔢 Steps: {len(steps)}")
                
                for i, step in enumerate(steps, 1):
                    desc = step.get('description', 'Unknown')
                    action = step.get('action_type', 'Unknown')
                    print(f"  {i}. {desc} ({action})")
            else:
                print("❌ Plan creation failed")
                
        except Exception as e:
            print(f"❌ Plan creator error: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_llm_performance()) 
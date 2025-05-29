#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from real_agent_automation_handler import RealAgentAutomationHandler

async def test_llm_planning_direct():
    """Test LLM planning directly"""
    print("🧪 Testing LLM Planning Directly")
    print("="*50)
    
    # Create handler
    handler = RealAgentAutomationHandler()
    
    # Test message
    test_message = "find best flights between NYC to Miami"
    session_id = "test_direct"
    
    print(f"🔍 Testing message: {test_message}")
    print()
    
    try:
        # Call LLM planning directly
        print("🧠 Calling LLM planning method...")
        plan = await handler._create_universal_llm_plan(test_message, session_id)
        
        print(f"✅ LLM Plan Created:")
        print(f"   Title: {plan.title}")
        print(f"   Description: {plan.description}")
        print(f"   Steps: {len(plan.steps)}")
        print(f"   Duration: {plan.estimated_duration}s")
        print(f"   Complexity: {getattr(plan, 'complexity_score', 'N/A')}")
        print()
        
        print("📋 Detailed Steps:")
        for i, step in enumerate(plan.steps, 1):
            print(f"   {i}. {step.description}")
            print(f"      Action: {step.action_type}")
            print(f"      Target: {step.target}")
            print(f"      Value: {step.value}")
            print(f"      Duration: {step.estimated_duration}s")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Planning Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_planning_direct())
    
    if success:
        print("🎉 LLM Planning Test: SUCCESS")
        print("   The LLM is generating comprehensive automation plans!")
    else:
        print("❌ LLM Planning Test: FAILED")
        print("   The LLM is not working properly for automation planning")
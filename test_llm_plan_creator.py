#!/usr/bin/env python3
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_plan_creator import LLMPlanCreator

async def test_llm_plan_creator():
    print("🧪 Testing LLM-Powered Plan Creator...")
    
    creator = LLMPlanCreator()
    
    # Test cases
    test_cases = [
        "Search Segev in Google",
        "Open Calculator and calculate 15 * 23",
        "Open TextEdit and write 'Hello World'",
        "Click on the center of the screen",
        "Open Safari and go to apple.com"
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: '{test_case}'")
        
        try:
            result = await creator.create_llm_plan(test_case, "test_session")
            
            print(f"✅ Success: {result.get('success', False)}")
            print(f"📋 Plan ID: {result.get('plan_id', 'None')}")
            
            if result.get('success') and result.get('plan'):
                plan = result['plan']
                steps = plan.get('steps', [])
                print(f"🔢 Steps: {len(steps)}")
                print(f"🤖 LLM Reasoning: {plan.get('llm_reasoning', 'None')[:100]}...")
                
                for i, step in enumerate(steps, 1):
                    description = step.get('description', 'Unknown')
                    action_type = step.get('action_type', 'Unknown')
                    value = step.get('value', '')
                    target = step.get('target', '')
                    reasoning = step.get('reasoning', '')
                    
                    print(f"  {i}. {description}")
                    print(f"     Action: {action_type}")
                    if value:
                        print(f"     Value: '{value}'")
                    if target:
                        print(f"     Target: '{target}'")
                    if reasoning:
                        print(f"     Reasoning: {reasoning}")
            else:
                print("❌ Plan creation failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_llm_plan_creator()) 
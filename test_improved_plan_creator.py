#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fixed_plan_creator import FixedPlanCreator

def test_improved_plan_creator():
    print("🧪 Testing Improved Plan Creator...")
    
    creator = FixedPlanCreator()
    
    # Test cases
    test_cases = [
        "Search Segev in Google",
        "Search for Segev",
        "Search Segev",
        "Open Safari and search for Segev",
        "Search for SEGEV in Google"
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: '{test_case}'")
        
        result = creator.create_accurate_plan(test_case, "test_session")
        
        print(f"✅ Success: {result.get('success', False)}")
        print(f"📋 Plan ID: {result.get('plan_id', 'None')}")
        
        if result.get('success') and result.get('plan'):
            plan = result['plan']
            steps = plan.get('steps', [])
            print(f"🔢 Steps: {len(steps)}")
            
            for i, step in enumerate(steps, 1):
                description = step.get('description', 'Unknown')
                action_type = step.get('action_type', 'Unknown')
                value = step.get('value', '')
                target = step.get('target', '')
                
                print(f"  {i}. {description}")
                print(f"     Action: {action_type}")
                if value:
                    print(f"     Value: '{value}'")
                if target:
                    print(f"     Target: '{target}'")
        else:
            print("❌ Plan creation failed")
        
        print("-" * 50)

if __name__ == "__main__":
    test_improved_plan_creator() 
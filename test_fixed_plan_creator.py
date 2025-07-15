#!/usr/bin/env python3
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fixed_plan_creator import FixedPlanCreator
    print("✅ FixedPlanCreator imported successfully")
    
    # Test the plan creator
    creator = FixedPlanCreator()
    print("✅ FixedPlanCreator instantiated successfully")
    
    # Test creating a plan
    result = creator.create_accurate_plan("Open Safari and search for SEGEV", "test_session")
    print("✅ Plan creation result:")
    print(f"  Success: {result.get('success', False)}")
    print(f"  Plan ID: {result.get('plan_id', 'None')}")
    print(f"  Steps: {len(result.get('steps', []))}")
    
    if result.get('success'):
        print("✅ Plan creation successful!")
        for i, step in enumerate(result.get('steps', []), 1):
            print(f"  {i}. {step.get('description', 'Unknown step')}")
    else:
        print("❌ Plan creation failed!")
        print(f"  Error: {result.get('response', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error testing FixedPlanCreator: {e}")
    import traceback
    traceback.print_exc() 
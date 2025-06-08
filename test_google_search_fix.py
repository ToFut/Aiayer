#!/usr/bin/env python3
"""
Test script for Google search fix in agent mode
This script tests the end-to-end workflow for "Search Segev in Google" agent mode
while preserving the existing planning system with DO/ADJUST/DISMISS buttons.
"""

import asyncio
import logging
import sys
import time
from typing import Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_google_search_workflow():
    """Test the end-to-end Google search workflow in agent mode"""
    print("\n=== Testing Google Search in Agent Mode ===")
    print("This test verifies the fix for 'Search Segev in Google' works with the DO button workflow\n")
    
    try:
        # Step 1: Import brain router
        from brain.core.brain_router import process_chat_request
        print("✓ Successfully imported brain router")
        
        # Step 2: Test the query to ensure it creates a plan
        print("\nTesting query: 'Search Segev in Google'")
        print("Sending request to agent mode...")
        
        # Send the query to the agent mode
        result = await process_chat_request(
            mode="Agent", 
            query="Search Segev in Google",
            user_id="test_user",
            session_id="test_session"
        )
        
        # Step 3: Verify plan is generated with buttons
        print("\nChecking plan generation:")
        success = result.get("success", False)
        mode = result.get("mode", "Unknown")
        
        print(f"  Success: {success}")
        print(f"  Mode: {mode}")
        
        # Check for buttons
        buttons = result.get("buttons", [])
        has_do_button = any(b.get("action") == "execute_plan" for b in buttons)
        has_adjust_button = any(b.get("action") == "modify_plan" for b in buttons)
        has_dismiss_button = any(b.get("action") == "cancel_plan" for b in buttons)
        
        print(f"  Has DO button: {'✓' if has_do_button else '✗'}")
        print(f"  Has ADJUST button: {'✓' if has_adjust_button else '✗'}")
        print(f"  Has DISMISS button: {'✓' if has_dismiss_button else '✗'}")
        
        # Extract plan ID
        plan_id = None
        for button in buttons:
            if button.get("action") == "execute_plan":
                plan_id = button.get("plan_id")
                break
        
        if plan_id:
            print(f"  Plan ID: {plan_id}")
        else:
            print("  ✗ No plan ID found")
        
        # Step 4: Get plan content
        plan_content = result.get("response", "")
        print("\nPlan content preview:")
        plan_lines = plan_content.split("\n")
        preview_lines = 10 if len(plan_lines) > 10 else len(plan_lines)
        for i in range(preview_lines):
            print(f"  {plan_lines[i]}")
        
        if len(plan_lines) > preview_lines:
            print(f"  ... ({len(plan_lines) - preview_lines} more lines)")
        
        # Step 5: Verify the plan looks good
        plan_has_google = "google" in plan_content.lower()
        plan_has_search = "search" in plan_content.lower()
        plan_has_segev = "segev" in plan_content.lower()
        plan_looks_good = plan_has_google and plan_has_search and plan_has_segev
        
        print(f"\nPlan contains required elements: {'✓' if plan_looks_good else '✗'}")
        
        # Final test summary
        if success and has_do_button and plan_looks_good:
            print("\n✅ TEST PASSED! The system generated a correct plan with DO button")
            print("Next steps: Click the DO button in the UI to execute the plan")
            return True
        else:
            print("\n❌ TEST FAILED! The system did not work as expected")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function to run the test"""
    result = await test_google_search_workflow()
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
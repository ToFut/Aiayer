#!/usr/bin/env python3
"""
Test the enhanced Professional Agent System with detailed sub-plans
"""

import asyncio
import logging
from professional_agent_system import ProfessionalAgentSystem

logging.basicConfig(level=logging.INFO)

async def test_agent_system():
    """Test the professional agent system"""
    try:
        # Initialize agent
        agent = ProfessionalAgentSystem()
        
        # Test request
        user_request = "Click the search button and search for 'test'"
        
        print("🚀 Testing Professional Agent System")
        print(f"Request: {user_request}")
        print("=" * 50)
        
        # Stage 1: Analyze and Plan
        print("📋 Stage 1: Analyzing and planning...")
        result = await agent.start_agent_session(user_request)
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"✅ Plan generated!")
        print(f"Session ID: {result['session_id']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Estimated Duration: {result['estimated_duration']}s")
        
        # Check if we have detailed plan
        execution_plan = result.get('execution_plan', {})
        if execution_plan.get('main_phases'):
            print("\n🎯 DETAILED SUB-PLANS:")
            for phase_idx, phase in enumerate(execution_plan['main_phases']):
                print(f"\n  Phase {phase_idx + 1}: {phase.get('phase_name', 'Unknown')}")
                print(f"    Description: {phase.get('phase_description', 'N/A')}")
                print(f"    Duration: {phase.get('estimated_duration', 0)}s")
                
                for sub_plan_idx, sub_plan in enumerate(phase.get('sub_plans', [])):
                    print(f"\n    Sub-plan {sub_plan_idx + 1}: {sub_plan.get('sub_plan_name', 'Unknown')}")
                    print(f"      Description: {sub_plan.get('sub_plan_description', 'N/A')}")
                    print(f"      Expected Outcome: {sub_plan.get('expected_outcome', 'N/A')}")
                    print(f"      Steps: {len(sub_plan.get('steps', []))}")
                    
                    for step_idx, step in enumerate(sub_plan.get('steps', [])):
                        print(f"        Step {step_idx + 1}: {step.get('description', 'N/A')}")
                        print(f"          Action: {step.get('action_type', 'N/A')}")
                        print(f"          Expected Result: {step.get('expected_result', 'N/A')}")
        
        print("\n🎯 CONFIRMATION REQUIRED")
        print("Available actions: DO, DISMISS, ADJUST")
        
        # For testing, automatically approve with DO
        print("\n📋 Stage 2: Auto-approving with DO...")
        exec_result = await agent.handle_user_confirmation(
            result['session_id'], 
            "DO"
        )
        
        if exec_result.get("error"):
            print(f"❌ Execution Error: {exec_result['error']}")
        else:
            print(f"✅ Execution completed!")
            print(f"Success: {exec_result.get('success', False)}")
            if exec_result.get('phase_results'):
                print("Phase Results:")
                for phase_result in exec_result['phase_results']:
                    print(f"  - {phase_result['phase_name']}: {'✅' if phase_result['success'] else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_system())
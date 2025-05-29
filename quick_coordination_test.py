#!/usr/bin/env python3
"""
Quick AgentMode Coordination Test - 3 Fast Tests
"""

import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_test():
    """Quick test of 3 different automation types"""
    
    print("🚀 Quick AgentMode Coordination Test")
    print("=" * 50)
    
    try:
        from real_agent_automation_handler import real_agent_handler
        
        # 3 quick test messages
        tests = [
            "open Calculator",
            "open TextEdit", 
            "open Terminal"
        ]
        
        results = []
        
        for i, message in enumerate(tests, 1):
            print(f"\n📝 Test {i}: {message}")
            print("-" * 30)
            
            session_id = f"test_{i}_{int(time.time())}"
            
            # Test plan creation
            start = time.time()
            plan_result = await real_agent_handler.handle_agent_request(message, session_id)
            plan_time = time.time() - start
            
            if plan_result["success"]:
                print(f"✅ Plan created in {plan_time:.1f}s")
                print(f"   Plan ID: {plan_result.get('plan_id', 'Unknown')}")
                print(f"   Interactive: {plan_result.get('interactive', False)}")
                print(f"   Automation Available: {plan_result.get('automation_available', False)}")
                
                # Test execution (DO button)
                if plan_result.get('plan_id'):
                    exec_start = time.time()
                    exec_result = await real_agent_handler.handle_button_action(
                        "execute_plan", 
                        plan_result['plan_id'], 
                        session_id
                    )
                    exec_time = time.time() - exec_start
                    
                    if exec_result["success"]:
                        print(f"✅ Execution completed in {exec_time:.1f}s")
                        print(f"   Success Rate: {exec_result.get('success_rate', 0):.1f}%")
                        results.append({"test": i, "plan": True, "exec": True})
                    else:
                        print(f"❌ Execution failed: {exec_result.get('response', 'Unknown')}")
                        results.append({"test": i, "plan": True, "exec": False})
                else:
                    print("❌ No plan ID for execution")
                    results.append({"test": i, "plan": True, "exec": False})
            else:
                print(f"❌ Plan failed: {plan_result.get('response', 'Unknown')}")
                results.append({"test": i, "plan": False, "exec": False})
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Results summary
        print("\n" + "=" * 50)
        print("📊 QUICK TEST SUMMARY")
        print("=" * 50)
        
        successful_plans = sum(1 for r in results if r["plan"])
        successful_execs = sum(1 for r in results if r["exec"])
        
        print(f"Plan Creation: {successful_plans}/{len(tests)} tests")
        print(f"Plan Execution: {successful_execs}/{len(tests)} tests")
        
        if successful_plans == len(tests) and successful_execs == len(tests):
            print("🟢 EXCELLENT: AgentMode coordination fully working!")
        elif successful_plans == len(tests):
            print("🟡 GOOD: Plans working, execution needs improvement")
        else:
            print("🔴 NEEDS WORK: Coordination issues detected")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(quick_test())
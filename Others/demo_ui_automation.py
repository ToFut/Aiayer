#!/usr/bin/env python3
"""
Demo: Agent Mode UI Automation
Shows real mouse and keyboard control through Agent mode
"""

import asyncio
import logging
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Others'))

from enterprise_workflow_engine import execute_agent_workflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_ui_automation():
    """Demonstrate UI automation capabilities"""
    
    print("🎭 Agent Mode UI Automation Demo")
    print("=" * 50)
    
    # Test cases showcasing UI automation
    test_cases = [
        {
            "name": "Basic Click Test",
            "query": "click at position 100 100",
            "description": "Simple mouse click at coordinates"
        },
        {
            "name": "Text Input Test", 
            "query": "type hello world",
            "description": "Keyboard text input"
        },
        {
            "name": "Complex Workflow",
            "query": "click at 150 150 then type AI Assistant and press return",
            "description": "Multi-step UI automation workflow"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Description: {test['description']}")
        print(f"   Command: {test['query']}")
        print("   " + "-" * 40)
        
        try:
            result = await execute_agent_workflow(test["query"], {
                "mode": "Agent",
                "user_id": "demo_user",
                "session_id": "ui_demo"
            })
            
            success = result.get("success", False)
            analysis = result.get("analysis", {})
            task_category = analysis.get("task_category", "unknown")
            
            print(f"   ✅ Category detected: {task_category}")
            print(f"   ✅ Execution success: {success}")
            
            if success and "execution_result" in result:
                exec_result = result["execution_result"]
                completed = exec_result.get("completed_steps", 0)
                total = exec_result.get("total_steps", 0)
                print(f"   ✅ Steps completed: {completed}/{total}")
                
                # Show specific UI actions performed
                if "results" in exec_result:
                    ui_actions = []
                    for step_id, step_result in exec_result["results"].items():
                        action = step_result.get("action")
                        if action in ["click", "type", "key_press"]:
                            if action == "click":
                                coords = step_result.get("coordinates", {})
                                ui_actions.append(f"Clicked at ({coords.get('x')}, {coords.get('y')})")
                            elif action == "type":
                                text = step_result.get("text", "")
                                ui_actions.append(f"Typed: '{text}'")
                            elif action == "key_press":
                                key = step_result.get("key", "")
                                ui_actions.append(f"Pressed: {key}")
                    
                    if ui_actions:
                        print("   🖱️ UI Actions performed:")
                        for action in ui_actions:
                            print(f"      • {action}")
            
            if "response" in result:
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                print(f"   💬 Response: {response_preview}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    print("🎉 Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("• Real mouse click execution")
    print("• Real keyboard text input")
    print("• Multi-step UI automation workflows")
    print("• Enterprise-grade Agent mode integration")
    print("• Safe UI automation with AppleScript backend")

if __name__ == "__main__":
    asyncio.run(demo_ui_automation())
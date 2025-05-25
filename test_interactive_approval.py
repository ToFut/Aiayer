#!/usr/bin/env python3
"""
Test script for the new interactive approval system in Agent mode.
This demonstrates the DO/Dismiss/Adjust workflow.
"""

import asyncio
import logging
import os
from enhanced_agent_automation import EnhancedAgentAutomation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_interactive_approval')

async def test_interactive_approval():
    """Test the interactive approval system"""
    try:
        logger.info("🚀 Testing Interactive Approval System for Agent Mode")
        
        # Initialize automation system
        automation = EnhancedAgentAutomation()
        
        # Test commands with different approval scenarios
        test_scenarios = [
            {
                "command": "click the close button",
                "auto_approve": True,
                "description": "Auto-approve scenario"
            },
            {
                "command": "click the calculator button", 
                "auto_approve": False,
                "description": "Interactive approval scenario"
            }
        ]
        
        for scenario in test_scenarios:
            logger.info(f"\n🎯 Testing: {scenario['description']}")
            logger.info(f"Command: '{scenario['command']}'")
            
            # Set approval mode
            os.environ["AGENT_AUTO_APPROVE"] = str(scenario["auto_approve"]).lower()
            
            try:
                # Execute command with interactive approval
                result = await automation.execute_command(scenario["command"])
                
                logger.info(f"📊 Result: {result.get('success', False)}")
                
                if result.get("success"):
                    logger.info(f"✅ Successfully executed: {result.get('action', 'unknown')}")
                    logger.info(f"   Target: {result.get('target_element', {}).get('text', 'unknown')}")
                    logger.info(f"   User choice: {result.get('user_choice', 'unknown')}")
                    
                    if "execution_plan" in result:
                        plan = result["execution_plan"]
                        target = plan.get("target_element", {})
                        logger.info(f"   Coordinates: {target.get('coordinates', 'unknown')}")
                        logger.info(f"   Confidence: {target.get('confidence', 0):.2f}")
                        
                else:
                    logger.warning(f"⚠️ Execution failed: {result.get('error', 'unknown')}")
                    if result.get("user_choice") == "dismissed":
                        logger.info("   User dismissed the automation")
                    elif result.get("user_choice") == "adjust":
                        logger.info(f"   User requested adjustment: {result.get('adjustment_feedback', 'N/A')}")
                
            except Exception as e:
                logger.error(f"❌ Test scenario failed: {e}")
            
            # Small delay between scenarios
            await asyncio.sleep(1)
        
        logger.info("\n🏁 Interactive approval testing completed")
        
        # Show example of what the approval dialog would look like
        logger.info("\n📋 Example Approval Dialog Format:")
        logger.info("="*50)
        
        example_plan = {
            "command": "click the submit button",
            "action": "click",
            "target_element": {
                "text": "Submit",
                "type": "button",
                "confidence": 0.85,
                "coordinates": "(450, 300)",
                "source": "total_screen_analyzer"
            },
            "execution_details": {
                "will_click_at": (450, 300),
                "risk_level": "low",
                "reversible": True
            },
            "alternatives": [
                {"text": "Send", "type": "button", "confidence": 0.72},
                {"text": "Apply", "type": "button", "confidence": 0.68}
            ]
        }
        
        # Create automation instance to use the formatter
        example_text = automation._format_execution_plan(example_plan)
        logger.info(example_text)
        logger.info("="*50)
        logger.info("User options: [DO] [Dismiss] [Adjust]")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set up environment for testing
    os.environ["AGENT_AUTO_APPROVE"] = "true"  # Default to auto-approve for demos
    
    asyncio.run(test_interactive_approval())
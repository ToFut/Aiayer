#!/usr/bin/env python3
"""
Test script to verify the enhanced_agent_automation.py fix with total_screen_analyzer
Tests the automation system without the slow LLaVA timeouts.
"""

import asyncio
import logging
import time
from enhanced_agent_automation import EnhancedAgentAutomation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_automation_fix')

async def test_automation_speed():
    """Test the automation system speed with total_screen_analyzer"""
    try:
        logger.info("🚀 Testing Enhanced Agent Automation with Total Screen Analyzer")
        
        # Initialize automation system
        automation = EnhancedAgentAutomation()
        
        # Test screen analysis speed
        start_time = time.time()
        logger.info("📸 Analyzing current screen...")
        
        analysis_result = await automation._analyze_current_screen()
        
        analysis_duration = time.time() - start_time
        logger.info(f"⚡ Screen analysis completed in {analysis_duration:.2f} seconds")
        
        if analysis_result.get("success"):
            elements = analysis_result.get("elements", [])
            logger.info(f"✅ Found {len(elements)} UI elements")
            
            # Show some detected elements
            for i, element in enumerate(elements[:5]):  # Show first 5
                logger.info(f"  {i+1}. {element.get('element_type', 'unknown')} - "
                          f"'{element.get('element_text', 'N/A')}' "
                          f"(confidence: {element.get('confidence', 0):.2f}) "
                          f"[{element.get('source', 'unknown')}]")
            
            # Test command parsing and execution
            test_commands = [
                "click the calculator button",
                "open the calculator app",
                "click the close button"
            ]
            
            for command in test_commands:
                logger.info(f"🎯 Testing command: '{command}'")
                start_cmd_time = time.time()
                
                try:
                    result = await automation.execute_command(command)
                    cmd_duration = time.time() - start_cmd_time
                    
                    if result.get("success"):
                        logger.info(f"✅ Command executed successfully in {cmd_duration:.2f}s")
                        logger.info(f"   Action: {result.get('action_taken', 'N/A')}")
                    else:
                        logger.warning(f"⚠️ Command failed: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    logger.error(f"❌ Command execution error: {e}")
                
                # Small delay between commands
                await asyncio.sleep(1)
        else:
            logger.error(f"❌ Screen analysis failed: {analysis_result.get('error', 'Unknown error')}")
        
        logger.info("🏁 Test completed")
        
        # Performance summary
        if analysis_duration < 5:
            logger.info("✅ SUCCESS: Screen analysis is now fast (< 5 seconds)!")
        elif analysis_duration < 10:
            logger.info("⚠️ IMPROVED: Screen analysis is faster but could be better")
        else:
            logger.warning("❌ STILL SLOW: Screen analysis taking too long")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_automation_speed())
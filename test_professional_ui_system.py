#!/usr/bin/env python3
"""
Test script for the enhanced professional UI system
Tests the "write SEGEV in notepad" command with super professional UI recognition
"""

import asyncio
import logging
import sys
import os

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_agent_automation import EnhancedAgentAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/professional_ui_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('professional_ui_test')

async def test_professional_ui_system():
    """Test the professional UI system with notepad automation"""
    try:
        logger.info("🚀 Starting Professional UI System Test")
        logger.info("="*60)
        
        # Initialize the enhanced agent automation system
        agent = EnhancedAgentAutomation()
        
        # Test command: "write SEGEV in notepad"
        test_command = 'write "SEGEV" in notepad'
        
        logger.info(f"📝 Testing command: '{test_command}'")
        logger.info("This will test:")
        logger.info("  1. Professional UI detection system")
        logger.info("  2. Enhanced coordinate extraction")
        logger.info("  3. Visual verification before actions")
        logger.info("  4. Multi-step automation (find notepad → click text area → type)")
        logger.info("-"*60)
        
        # Execute the command
        result = await agent.execute_command(test_command)
        
        logger.info("-"*60)
        logger.info("📊 TEST RESULTS:")
        logger.info(f"Success: {result.get('success', False)}")
        
        if result.get("success"):
            logger.info("✅ PROFESSIONAL UI SYSTEM TEST PASSED!")
            
            # Log detailed results
            if result.get("execution_plan"):
                plan = result["execution_plan"]
                logger.info(f"Action executed: {plan.get('action', 'N/A')}")
                logger.info(f"Target element: {plan.get('target_element', {}).get('element_text', 'N/A')}")
                logger.info(f"Text typed: {plan.get('text_to_type', 'N/A')}")
            
            if result.get("visual_verification"):
                logger.info("🎯 Visual verification was performed")
            
            if result.get("verification"):
                verification = result["verification"]
                if verification.get("verified"):
                    logger.info("✅ Text typing verification: PASSED")
                else:
                    logger.info("⚠️ Text typing verification: INCONCLUSIVE")
                    
        else:
            logger.error("❌ PROFESSIONAL UI SYSTEM TEST FAILED!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            
            if result.get("details"):
                logger.error(f"Details: {result['details']}")
        
        logger.info("="*60)
        logger.info("🏁 Professional UI System Test Complete")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}

async def test_ui_detection_only():
    """Test just the UI detection without executing actions"""
    try:
        logger.info("🔍 Testing UI Detection Only (No Actions)")
        
        # Initialize the enhanced agent automation system
        agent = EnhancedAgentAutomation()
        
        # Capture and analyze current screen
        result = await agent._analyze_current_screen()
        
        if result.get("success"):
            elements = result.get("elements", [])
            logger.info(f"📍 Professional UI Detection found {len(elements)} elements")
            
            # Show top 10 elements found
            for i, element in enumerate(elements[:10]):
                logger.info(f"  {i+1}. {element.get('element_type', 'unknown')} - "
                          f"'{element.get('element_text', 'N/A')}' - "
                          f"confidence: {element.get('confidence', 0):.2f}")
            
            # Look for notepad-specific elements
            notepad_elements = [e for e in elements 
                             if 'notepad' in e.get('element_text', '').lower() or
                                e.get('element_type', '') in ['text_field', 'textarea', 'text_area']]
            
            if notepad_elements:
                logger.info(f"🎯 Found {len(notepad_elements)} notepad-related elements:")
                for element in notepad_elements:
                    logger.info(f"  - {element.get('element_type', 'unknown')}: "
                              f"'{element.get('element_text', 'N/A')}'")
            else:
                logger.info("⚠️ No notepad-related elements found")
                
        else:
            logger.error(f"❌ UI Detection failed: {result.get('error', 'Unknown error')}")
            
        return result
        
    except Exception as e:
        logger.error(f"💥 UI Detection test failed: {e}")
        return {"success": False, "error": str(e)}

async def main():
    """Main test function"""
    logger.info("🧪 PROFESSIONAL UI SYSTEM COMPREHENSIVE TEST")
    logger.info("="*70)
    
    # Test 1: UI Detection Only
    logger.info("\n📋 TEST 1: UI Detection Only")
    await test_ui_detection_only()
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Test 2: Full automation
    logger.info("\n🤖 TEST 2: Full Automation Test")
    result = await test_professional_ui_system()
    
    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
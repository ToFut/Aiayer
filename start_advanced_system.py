#!/usr/bin/env python3
"""
Start Advanced AI-RPA System
Leverages Aiayer's existing advanced capabilities:
- neural_ui_detector.py for state-of-the-art UI understanding
- universal_smart_planner.py for intelligent task planning
- universal_task_loop_controller.py for multi-task execution
- universal_intelligent_automation_handler.py for advanced automation
- RPA_AVEN server for real low-level execution
"""

import asyncio
import sys
import os
import time
import logging
from pathlib import Path

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("advanced_system")

async def start_advanced_system():
    """Start the complete advanced AI-RPA system"""
    logger.info("🚀 Starting Advanced AI-RPA System")
    logger.info("=" * 60)
    
    try:
        # Step 1: Import and test Aiayer's advanced components
        logger.info("📦 Testing Aiayer's advanced components...")
        
        # Test neural UI detector
        try:
            from neural_ui_detector import NeuralUIDetector
            ui_detector = NeuralUIDetector()
            logger.info("✅ Neural UI Detector loaded successfully")
        except Exception as e:
            logger.error(f"❌ Neural UI Detector failed: {e}")
            return False
        
        # Test universal smart planner
        try:
            from universal_smart_planner import UniversalSmartPlanner
            smart_planner = UniversalSmartPlanner()
            logger.info("✅ Universal Smart Planner loaded successfully")
        except Exception as e:
            logger.error(f"❌ Universal Smart Planner failed: {e}")
            return False
        
        # Test universal task loop controller
        try:
            from universal_task_loop_controller import UniversalTaskLoopController
            task_controller = UniversalTaskLoopController()
            await task_controller.initialize()
            logger.info("✅ Universal Task Loop Controller loaded successfully")
        except Exception as e:
            logger.error(f"❌ Universal Task Loop Controller failed: {e}")
            return False
        
        # Test universal intelligent automation handler
        try:
            from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
            automation_handler = UniversalIntelligentAutomationHandler()
            logger.info("✅ Universal Intelligent Automation Handler loaded successfully")
        except Exception as e:
            logger.error(f"❌ Universal Intelligent Automation Handler failed: {e}")
            return False
        
        # Step 2: Test RPA_AVEN server connection
        logger.info("🔗 Testing RPA_AVEN server connection...")
        try:
            import requests
            response = requests.get("http://localhost:8080/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ RPA_AVEN server is running and responsive")
            else:
                logger.error(f"❌ RPA_AVEN server returned status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ RPA_AVEN server connection failed: {e}")
            logger.info("💡 Make sure to start the RPA_AVEN server first:")
            logger.info("   cd RPA_AVEN/helper && go run main_universal.go")
            return False
        
        # Step 3: Initialize advanced AI-RPA bridge
        logger.info("🌉 Initializing Advanced AI-RPA Bridge...")
        try:
            from integration.advanced_ai_rpa_bridge import initialize_advanced_bridge
            advanced_bridge = await initialize_advanced_bridge()
            logger.info("✅ Advanced AI-RPA Bridge initialized successfully")
        except Exception as e:
            logger.error(f"❌ Advanced AI-RPA Bridge failed: {e}")
            return False
        
        # Step 4: Test UI understanding capabilities
        logger.info("👁️ Testing UI understanding capabilities...")
        try:
            ui_understanding = await advanced_bridge.get_ui_understanding()
            if ui_understanding.get("success"):
                logger.info(f"✅ UI Understanding working: {ui_understanding.get('elements')} elements detected")
                logger.info(f"   Screen: {ui_understanding.get('screen_size')}")
                logger.info(f"   Methods: {', '.join(ui_understanding.get('detection_methods', []))}")
            else:
                logger.warning(f"⚠️ UI Understanding test failed: {ui_understanding.get('error')}")
        except Exception as e:
            logger.error(f"❌ UI Understanding test failed: {e}")
        
        # Step 5: Test advanced task execution
        logger.info("🧪 Testing advanced task execution...")
        try:
            from integration.advanced_ai_rpa_bridge import execute_advanced_task
            
            # Test with a simple task
            test_result = await execute_advanced_task("Open Calculator")
            
            if test_result.success:
                logger.info(f"✅ Advanced task execution successful!")
                logger.info(f"   Steps completed: {test_result.steps_completed}/{test_result.total_steps}")
                logger.info(f"   UI elements detected: {test_result.ui_elements_detected}")
                logger.info(f"   Execution time: {test_result.execution_time:.2f}s")
                if test_result.errors:
                    logger.warning(f"   Errors: {len(test_result.errors)}")
            else:
                logger.warning(f"⚠️ Advanced task execution had issues: {test_result.errors}")
                
        except Exception as e:
            logger.error(f"❌ Advanced task execution test failed: {e}")
        
        # Step 6: Start interactive mode
        logger.info("🎯 Starting interactive mode...")
        logger.info("💬 You can now use the system with advanced AI capabilities!")
        logger.info("📝 Example commands:")
        logger.info("   - 'Open Calculator and calculate 15 * 23'")
        logger.info("   - 'Open TextEdit and write a note about AI automation'")
        logger.info("   - 'Open Safari and search for Python automation tutorials'")
        logger.info("   - 'Open System Preferences and check display settings'")
        logger.info("")
        logger.info("🔧 Advanced features available:")
        logger.info("   - Neural UI detection with YOLOv8 and LayoutLM")
        logger.info("   - Intelligent task planning with LLM reasoning")
        logger.info("   - Multi-task execution with state persistence")
        logger.info("   - Real-time UI understanding and adaptation")
        logger.info("   - Error recovery and fallback strategies")
        logger.info("")
        logger.info("🚀 System is ready for advanced automation!")
        
        # Keep the system running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Shutting down Advanced AI-RPA System...")
        return True
    except Exception as e:
        logger.error(f"❌ System startup failed: {e}")
        return False

async def test_advanced_components():
    """Test individual advanced components"""
    logger.info("🧪 Testing Advanced Components")
    logger.info("=" * 40)
    
    # Test neural UI detector
    logger.info("1. Testing Neural UI Detector...")
    try:
        from neural_ui_detector import NeuralUIDetector
        detector = NeuralUIDetector()
        result = await detector.detect_elements()
        logger.info(f"   ✅ Detected {len(result.elements)} UI elements")
        logger.info(f"   📊 Screen: {result.screen_width}x{result.screen_height}")
        logger.info(f"   ⏱️ Time: {result.execution_time:.2f}s")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
    
    # Test smart planner
    logger.info("2. Testing Universal Smart Planner...")
    try:
        from universal_smart_planner import UniversalSmartPlanner
        planner = UniversalSmartPlanner()
        plan = await planner.create_universal_plan("Open Calculator and calculate 10 + 5", "test_session")
        logger.info(f"   ✅ Created plan with {len(plan.steps)} steps")
        logger.info(f"   📋 Title: {plan.title}")
        logger.info(f"   ⏱️ Estimated duration: {plan.estimated_duration:.1f}s")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
    
    # Test task controller
    logger.info("3. Testing Universal Task Loop Controller...")
    try:
        from universal_task_loop_controller import UniversalTaskLoopController
        controller = UniversalTaskLoopController()
        await controller.initialize()
        logger.info("   ✅ Task controller initialized")
        
        # Submit a test task
        task_result = await controller.submit_task("Test task", "universal")
        logger.info(f"   ✅ Submitted task: {task_result.get('task_id')}")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
    
    # Test automation handler
    logger.info("4. Testing Universal Intelligent Automation Handler...")
    try:
        from universal_intelligent_automation_handler import UniversalIntelligentAutomationHandler
        handler = UniversalIntelligentAutomationHandler()
        result = await handler.create_universal_automation_plan("Open Calculator", "test_session")
        logger.info(f"   ✅ Created automation plan: {result.get('success')}")
        if result.get('success'):
            logger.info(f"   📋 Plan ID: {result.get('plan_id')}")
            logger.info(f"   🎯 Request type: {result.get('request_type')}")
    except Exception as e:
        logger.error(f"   ❌ Failed: {e}")
    
    logger.info("=" * 40)
    logger.info("✅ Advanced component testing completed!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Advanced AI-RPA System")
    parser.add_argument("--test", action="store_true", help="Test advanced components only")
    parser.add_argument("--start", action="store_true", help="Start the complete system")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_advanced_components())
    elif args.start:
        asyncio.run(start_advanced_system())
    else:
        # Default: start the system
        asyncio.run(start_advanced_system()) 
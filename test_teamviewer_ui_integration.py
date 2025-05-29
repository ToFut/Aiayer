#!/usr/bin/env python3
"""
Test TeamViewer UI Integration
Validates that the system can detect UI elements and execute clicks properly
"""

import asyncio
import json
import time
import logging
from teamviewer_ui_automation_system import TeamViewerUIAutomationSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ui_detection():
    """Test UI element detection capabilities"""
    system = TeamViewerUIAutomationSystem(teamviewer_enabled=True)
    
    logger.info("🔍 Testing UI element detection...")
    
    # Test screen capture
    screenshot = await system.capture_screen()
    if screenshot.size > 0:
        logger.info(f"✅ Screen capture successful: {screenshot.shape}")
    else:
        logger.error("❌ Screen capture failed")
        return False
    
    # Test UI element detection
    elements = await system.detect_ui_elements(screenshot)
    logger.info(f"🎯 Detected {len(elements)} UI elements")
    
    for i, element in enumerate(elements[:5]):  # Show first 5
        logger.info(f"   {i+1}. {element.element_type} at {element.center} (confidence: {element.confidence:.2f})")
    
    return len(elements) > 0

async def test_automation_plan_creation():
    """Test automation plan creation"""
    system = TeamViewerUIAutomationSystem(teamviewer_enabled=True)
    
    logger.info("📝 Testing automation plan creation...")
    
    # Test plan creation
    test_messages = [
        "click the calculator button",
        "type hello world in the search box",
        "open Safari and navigate to YouTube"
    ]
    
    for message in test_messages:
        logger.info(f"🧠 Creating plan for: '{message}'")
        plan_result = await system.create_automation_plan(message, "agent", "test_session")
        
        if plan_result.get("type") == "plan_created":
            plan = plan_result["plan"]
            logger.info(f"✅ Plan created: {plan['title']} ({len(plan['steps'])} steps)")
        else:
            logger.error(f"❌ Plan creation failed: {plan_result}")
            return False
    
    return True

async def test_teamviewer_integration():
    """Test TeamViewer integration features"""
    system = TeamViewerUIAutomationSystem(teamviewer_enabled=True)
    
    logger.info("🖥️ Testing TeamViewer integration...")
    
    # Test ID generation
    id_result = await system.handle_teamviewer_action("generate_id")
    if id_result.get("type") == "teamviewer_id_generated":
        logger.info(f"✅ TeamViewer ID generated: {id_result['formatted_id']}")
    else:
        logger.error(f"❌ ID generation failed: {id_result}")
        return False
    
    # Test screen sharing
    share_result = await system.handle_teamviewer_action("start_screen_share")
    if share_result.get("type") == "screen_sharing_started":
        logger.info("✅ Screen sharing simulation successful")
    else:
        logger.error(f"❌ Screen sharing failed: {share_result}")
        return False
    
    # Test remote control
    control_result = await system.handle_teamviewer_action("enable_remote_control")
    if control_result.get("type") == "remote_control_enabled":
        logger.info("✅ Remote control simulation successful")
    else:
        logger.error(f"❌ Remote control failed: {control_result}")
        return False
    
    return True

async def test_click_execution():
    """Test actual click execution (be careful - this will click on screen!)"""
    system = TeamViewerUIAutomationSystem(teamviewer_enabled=True)
    
    logger.info("🎯 Testing click execution...")
    logger.info("⚠️ This will perform an actual click - make sure screen is safe!")
    
    # Wait a moment for user to prepare
    await asyncio.sleep(2)
    
    # Test safe coordinates (middle of screen, away from critical UI)
    import pyautogui
    screen_width, screen_height = pyautogui.size()
    safe_x = screen_width // 2
    safe_y = screen_height // 2
    
    logger.info(f"🎯 Executing test click at safe coordinates ({safe_x}, {safe_y})")
    
    click_result = await system.execute_click_action((safe_x, safe_y), "test_element")
    
    if click_result.get("type") == "click_success":
        logger.info("✅ Click execution successful")
        validation = click_result.get("validation", {})
        if validation.get("change_detected"):
            logger.info(f"✅ Screen change detected: {validation.get('change_percentage', 0)*100:.1f}%")
        else:
            logger.info("ℹ️ No significant screen change detected")
    else:
        logger.error(f"❌ Click execution failed: {click_result}")
        return False
    
    return True

async def test_websocket_messages():
    """Test WebSocket message handling"""
    system = TeamViewerUIAutomationSystem(teamviewer_enabled=True)
    
    logger.info("📡 Testing WebSocket message handling...")
    
    # Mock WebSocket object for testing
    class MockWebSocket:
        def __init__(self):
            self.messages = []
        
        async def send(self, message):
            self.messages.append(json.loads(message))
    
    mock_ws = MockWebSocket()
    
    # Test create plan message
    await system.handle_websocket_message({
        "type": "create_plan",
        "message": "click the test button",
        "mode": "agent",
        "session_id": "test_123"
    }, mock_ws)
    
    if mock_ws.messages:
        response = mock_ws.messages[0]
        logger.info(f"✅ Plan creation message handled: {response.get('type')}")
    else:
        logger.error("❌ No response to plan creation message")
        return False
    
    # Test UI detection message
    mock_ws.messages.clear()
    await system.handle_websocket_message({
        "type": "detect_ui_elements"
    }, mock_ws)
    
    if mock_ws.messages:
        response = mock_ws.messages[0]
        logger.info(f"✅ UI detection message handled: {response.get('type')}")
    else:
        logger.error("❌ No response to UI detection message")
        return False
    
    return True

async def run_integration_tests():
    """Run all integration tests"""
    logger.info("🚀 Starting TeamViewer UI Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("UI Detection", test_ui_detection),
        ("Automation Plan Creation", test_automation_plan_creation),
        ("TeamViewer Integration", test_teamviewer_integration),
        ("WebSocket Message Handling", test_websocket_messages),
        # ("Click Execution", test_click_execution),  # Commented out for safety
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🔬 Running test: {test_name}")
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All tests passed! System is ready for use.")
        logger.info("🌐 Run './start_teamviewer_ui_test.sh' to start the full system")
    else:
        logger.warning(f"⚠️ {failed} tests failed. Please check the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    try:
        result = asyncio.run(run_integration_tests())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Tests interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"💥 Test execution failed: {e}")
        exit(1)
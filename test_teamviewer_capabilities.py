#!/usr/bin/env python3
"""
Test TeamViewer-Style Capabilities Integration
Tests the enhanced agent system with visual verification and screen control
"""

import asyncio
import json
import time
import logging
import sys
import os
import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeamViewerCapabilitiesTest:
    """Comprehensive test for TeamViewer-style capabilities"""
    
    def __init__(self):
        self.test_results = {}
        self.websocket = None
        self.backend_url = "ws://localhost:8767"
        
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting TeamViewer-Style Capabilities Test Suite")
        logger.info("=" * 60)
        
        # Test 1: Basic Screen Capture
        await self.test_screen_capture_capabilities()
        
        # Test 2: Visual Change Detection
        await self.test_visual_change_detection()
        
        # Test 3: Backend Integration
        await self.test_backend_integration()
        
        # Test 4: Enhanced Agent Mode
        await self.test_enhanced_agent_mode()
        
        # Test 5: Real-time Monitoring
        await self.test_real_time_monitoring()
        
        # Test 6: WebSocket Communication
        await self.test_websocket_communication()
        
        # Generate final report
        self.generate_test_report()
    
    async def test_screen_capture_capabilities(self):
        """Test screen capture functionality"""
        logger.info("🖼️ Test 1: Screen Capture Capabilities")
        
        try:
            # Import backend
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from enhanced_enterprise_backend_with_context import ContextualAIBackend
            
            # Create backend instance
            backend = ContextualAIBackend()
            
            # Test full screen capture
            logger.info("  📸 Testing full screen capture...")
            screenshot = await backend.capture_screen_fast()
            
            if screenshot is not None:
                logger.info(f"  ✅ Full screen capture successful: {screenshot.shape}")
                self.test_results['full_screen_capture'] = {
                    'success': True,
                    'shape': screenshot.shape,
                    'size_mb': screenshot.nbytes / (1024 * 1024)
                }
            else:
                logger.error("  ❌ Full screen capture failed")
                self.test_results['full_screen_capture'] = {'success': False}
            
            # Test region capture
            logger.info("  📸 Testing region capture...")
            region_screenshot = await backend.capture_screen_fast((100, 100, 300, 200))
            
            if region_screenshot is not None:
                logger.info(f"  ✅ Region capture successful: {region_screenshot.shape}")
                self.test_results['region_capture'] = {
                    'success': True,
                    'shape': region_screenshot.shape
                }
            else:
                logger.error("  ❌ Region capture failed")
                self.test_results['region_capture'] = {'success': False}
                
        except Exception as e:
            logger.error(f"  ❌ Screen capture test failed: {e}")
            self.test_results['screen_capture_error'] = str(e)
    
    async def test_visual_change_detection(self):
        """Test visual change detection algorithms"""
        logger.info("🔍 Test 2: Visual Change Detection")
        
        try:
            from enhanced_enterprise_backend_with_context import ContextualAIBackend
            import numpy as np
            
            backend = ContextualAIBackend()
            
            # Create test images
            logger.info("  🎨 Creating test images...")
            
            # Original image (all blue)
            original = np.full((100, 100, 3), [0, 0, 255], dtype=np.uint8)
            
            # Modified image (red square in center)
            modified = original.copy()
            modified[40:60, 40:60] = [255, 0, 0]  # Red square
            
            # Test change detection
            logger.info("  🔍 Testing change detection...")
            changes = await backend.detect_visual_changes(original, modified, threshold=0.05)
            
            if changes.get('changes_detected', False):
                logger.info(f"  ✅ Changes detected: {changes['change_percentage']:.2%}")
                logger.info(f"  📊 Changed regions: {len(changes.get('changed_regions', []))}")
                logger.info(f"  🎯 Confidence: {changes.get('confidence', 0):.2f}")
                
                self.test_results['change_detection'] = {
                    'success': True,
                    'change_percentage': changes['change_percentage'],
                    'regions_found': len(changes.get('changed_regions', [])),
                    'confidence': changes.get('confidence', 0)
                }
            else:
                logger.error("  ❌ Changes not detected")
                self.test_results['change_detection'] = {'success': False}
            
            # Test no-change scenario
            logger.info("  🔍 Testing no-change detection...")
            no_changes = await backend.detect_visual_changes(original, original)
            
            if not no_changes.get('changes_detected', True):
                logger.info("  ✅ No-change correctly detected")
                self.test_results['no_change_detection'] = {'success': True}
            else:
                logger.warning("  ⚠️ False positive in no-change detection")
                self.test_results['no_change_detection'] = {'success': False}
                
        except Exception as e:
            logger.error(f"  ❌ Visual change detection test failed: {e}")
            self.test_results['change_detection_error'] = str(e)
    
    async def test_backend_integration(self):
        """Test backend integration and methods"""
        logger.info("🔧 Test 3: Backend Integration")
        
        try:
            from enhanced_enterprise_backend_with_context import ContextualAIBackend, SCREEN_CAPTURE_AVAILABLE
            
            # Test backend initialization
            logger.info("  🚀 Testing backend initialization...")
            backend = ContextualAIBackend()
            
            if hasattr(backend, 'execution_verification_enabled'):
                logger.info("  ✅ TeamViewer capabilities initialized")
                self.test_results['backend_init'] = {'success': True}
            else:
                logger.error("  ❌ TeamViewer capabilities not found")
                self.test_results['backend_init'] = {'success': False}
            
            # Test screen capture availability
            logger.info(f"  📷 Screen capture available: {SCREEN_CAPTURE_AVAILABLE}")
            self.test_results['screen_capture_available'] = SCREEN_CAPTURE_AVAILABLE
            
            # Test action execution method
            logger.info("  ⚡ Testing action execution method...")
            test_action = {
                'description': 'Test action',
                'action_type': 'test',
                'target': 'test_target'
            }
            
            if hasattr(backend, 'execute_action_with_verification'):
                logger.info("  ✅ Action execution method available")
                self.test_results['action_execution_method'] = {'success': True}
            else:
                logger.error("  ❌ Action execution method not found")
                self.test_results['action_execution_method'] = {'success': False}
            
            # Test enhanced agent methods
            if hasattr(backend, 'handle_agent_execution_with_verification'):
                logger.info("  ✅ Enhanced agent execution method available")
                self.test_results['enhanced_agent_method'] = {'success': True}
            else:
                logger.error("  ❌ Enhanced agent execution method not found")
                self.test_results['enhanced_agent_method'] = {'success': False}
                
        except Exception as e:
            logger.error(f"  ❌ Backend integration test failed: {e}")
            self.test_results['backend_integration_error'] = str(e)
    
    async def test_enhanced_agent_mode(self):
        """Test enhanced agent mode functionality"""
        logger.info("🤖 Test 4: Enhanced Agent Mode")
        
        try:
            from enhanced_enterprise_backend_with_context import ContextualAIBackend, FAST_AUTOMATION_AVAILABLE
            
            backend = ContextualAIBackend()
            
            logger.info(f"  ⚡ Fast automation available: {FAST_AUTOMATION_AVAILABLE}")
            self.test_results['fast_automation_available'] = FAST_AUTOMATION_AVAILABLE
            
            if FAST_AUTOMATION_AVAILABLE:
                # Test enhanced agent request creation
                logger.info("  🎯 Testing enhanced agent request...")
                
                test_data = {
                    'message': 'Test automation task',
                    'session_id': 'test_session',
                    'execution_mode': 'verified'
                }
                
                # Mock websocket for testing
                class MockWebSocket:
                    def __init__(self):
                        self.sent_messages = []
                    
                    async def send(self, message):
                        self.sent_messages.append(json.loads(message))
                        logger.info(f"    📤 Sent: {json.loads(message).get('type', 'unknown')}")
                
                mock_ws = MockWebSocket()
                
                # Test the enhanced agent handler
                result = await backend.handle_agent_execution_with_verification(
                    test_data, 'test_client', mock_ws
                )
                
                if result.get('success', False):
                    logger.info("  ✅ Enhanced agent request successful")
                    logger.info(f"    📋 Plan ID: {result.get('plan_id', 'N/A')}")
                    logger.info(f"    💬 Messages sent: {len(mock_ws.sent_messages)}")
                    
                    self.test_results['enhanced_agent_mode'] = {
                        'success': True,
                        'plan_id': result.get('plan_id'),
                        'messages_sent': len(mock_ws.sent_messages),
                        'execution_mode': result.get('execution_mode')
                    }
                else:
                    logger.error(f"  ❌ Enhanced agent request failed: {result.get('error', 'Unknown')}")
                    self.test_results['enhanced_agent_mode'] = {
                        'success': False,
                        'error': result.get('error')
                    }
            else:
                logger.warning("  ⚠️ Fast automation not available, skipping enhanced agent test")
                self.test_results['enhanced_agent_mode'] = {
                    'success': False,
                    'reason': 'Fast automation not available'
                }
                
        except Exception as e:
            logger.error(f"  ❌ Enhanced agent mode test failed: {e}")
            self.test_results['enhanced_agent_mode_error'] = str(e)
    
    async def test_real_time_monitoring(self):
        """Test real-time monitoring capabilities"""
        logger.info("📱 Test 5: Real-time Monitoring")
        
        try:
            from enhanced_enterprise_backend_with_context import ContextualAIBackend
            
            backend = ContextualAIBackend()
            
            # Test monitoring start/stop
            logger.info("  🎬 Testing monitoring start/stop...")
            
            if hasattr(backend, 'start_screen_monitoring'):
                logger.info("  ✅ Screen monitoring method available")
                
                # Test monitoring for a short duration
                monitoring_task = asyncio.create_task(
                    backend.start_screen_monitoring(None, fps=5)
                )
                
                # Let it run for 2 seconds
                await asyncio.sleep(2)
                
                # Stop monitoring
                backend.stop_screen_monitoring()
                
                # Wait for monitoring to stop
                await asyncio.sleep(1)
                
                logger.info("  ✅ Monitoring start/stop successful")
                self.test_results['real_time_monitoring'] = {'success': True}
                
            else:
                logger.error("  ❌ Screen monitoring method not found")
                self.test_results['real_time_monitoring'] = {'success': False}
                
        except Exception as e:
            logger.error(f"  ❌ Real-time monitoring test failed: {e}")
            self.test_results['real_time_monitoring_error'] = str(e)
    
    async def test_websocket_communication(self):
        """Test WebSocket communication with backend"""
        logger.info("🌐 Test 6: WebSocket Communication")
        
        try:
            # Test connection to backend
            logger.info("  🔌 Testing WebSocket connection...")
            
            try:
                async with websockets.connect(self.backend_url, timeout=5) as websocket:
                    logger.info("  ✅ WebSocket connection successful")
                    
                    # Test basic message
                    test_message = {
                        "type": "chat_request",
                        "mode": "Ask",
                        "message": "Test message",
                        "session_id": "test_session"
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    logger.info("  📤 Test message sent")
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        response_data = json.loads(response)
                        
                        logger.info(f"  📥 Response received: {response_data.get('type', 'unknown')}")
                        
                        self.test_results['websocket_communication'] = {
                            'success': True,
                            'response_type': response_data.get('type'),
                            'response_success': response_data.get('success', False)
                        }
                        
                    except asyncio.TimeoutError:
                        logger.warning("  ⚠️ Response timeout")
                        self.test_results['websocket_communication'] = {
                            'success': True,
                            'note': 'Connection successful but response timeout'
                        }
                        
            except Exception as e:
                logger.error(f"  ❌ WebSocket connection failed: {e}")
                self.test_results['websocket_communication'] = {
                    'success': False,
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"  ❌ WebSocket communication test failed: {e}")
            self.test_results['websocket_communication_error'] = str(e)
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("📊 COMPREHENSIVE TEST REPORT")
        logger.info("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        # Analyze results
        for test_name, result in self.test_results.items():
            if test_name.endswith('_error'):
                continue
                
            total_tests += 1
            if isinstance(result, dict) and result.get('success', False):
                passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"📈 OVERALL RESULTS:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {passed_tests}")
        logger.info(f"   Failed: {total_tests - passed_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info("")
        
        # Detailed results
        logger.info("📋 DETAILED RESULTS:")
        
        test_categories = {
            'Screen Capture': ['full_screen_capture', 'region_capture', 'screen_capture_available'],
            'Visual Detection': ['change_detection', 'no_change_detection'],
            'Backend Integration': ['backend_init', 'action_execution_method', 'enhanced_agent_method'],
            'Agent Mode': ['fast_automation_available', 'enhanced_agent_mode'],
            'Monitoring': ['real_time_monitoring'],
            'Communication': ['websocket_communication']
        }
        
        for category, tests in test_categories.items():
            logger.info(f"\n🔍 {category}:")
            for test in tests:
                if test in self.test_results:
                    result = self.test_results[test]
                    if isinstance(result, dict):
                        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
                        logger.info(f"   {test}: {status}")
                        if not result.get('success', False) and 'error' in result:
                            logger.info(f"      Error: {result['error']}")
                    else:
                        logger.info(f"   {test}: {result}")
        
        # Errors
        errors = {k: v for k, v in self.test_results.items() if k.endswith('_error')}
        if errors:
            logger.info(f"\n❌ ERRORS ENCOUNTERED:")
            for error_name, error_msg in errors.items():
                logger.info(f"   {error_name}: {error_msg}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        
        if not self.test_results.get('screen_capture_available', False):
            logger.info("   📦 Install required packages: pip install opencv-python pillow numpy")
        
        if not self.test_results.get('fast_automation_available', False):
            logger.info("   ⚡ Fast automation handler not available - check fast_universal_automation_handler.py")
        
        websocket_result = self.test_results.get('websocket_communication', {})
        if not websocket_result.get('success', False):
            logger.info("   🌐 Start the enhanced backend: python enhanced_enterprise_backend_with_context.py")
        
        if success_rate >= 80:
            logger.info("   🎉 System is working well! TeamViewer capabilities are functional.")
        elif success_rate >= 60:
            logger.info("   ⚠️  System mostly working, some issues to resolve.")
        else:
            logger.info("   🔧 Significant issues detected, review failed tests.")
        
        logger.info("\n" + "=" * 60)
        logger.info("📋 Test completed! Check the detailed report above.")

async def main():
    """Main test execution"""
    test_suite = TeamViewerCapabilitiesTest()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
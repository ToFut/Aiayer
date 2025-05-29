#!/usr/bin/env python3
"""
Test Real-Time TeamViewer-Style System
Tests the complete real-time screen sharing and agent vision system
"""

import asyncio
import time
import logging
import json
from typing import Dict, Any

# Import our real-time components
from realtime_screen_tcp_server import RealTimeScreenTCPServer
from realtime_agent_vision import RealTimeAgentVision

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTimeSystemTester:
    """Test the complete real-time TeamViewer-style system"""
    
    def __init__(self):
        self.server = RealTimeScreenTCPServer(host="localhost", port=9999)
        self.agent = RealTimeAgentVision(server_host="localhost", server_port=9999)
        self.test_results = {}
        
    async def test_complete_system(self):
        """Test the complete real-time system"""
        logger.info("🧪 Starting Real-Time TeamViewer System Test")
        logger.info("=" * 60)
        
        # Test 1: Start screen server
        await self._test_screen_server_startup()
        
        # Test 2: Agent connection
        await self._test_agent_connection()
        
        # Test 3: Real-time streaming
        await self._test_realtime_streaming()
        
        # Test 4: UI element detection
        await self._test_ui_detection()
        
        # Test 5: Agent action execution
        await self._test_agent_actions()
        
        # Test 6: Performance metrics
        await self._test_performance()
        
        # Print final results
        self._print_test_results()
        
        # Cleanup
        await self._cleanup()
    
    async def _test_screen_server_startup(self):
        """Test screen server startup"""
        test_name = "Screen Server Startup"
        logger.info(f"🔄 Testing: {test_name}")
        
        try:
            # Start server in background
            server_task = asyncio.create_task(self.server.start_server())
            
            # Give it time to start
            await asyncio.sleep(2)
            
            # Check if server is running
            if self.server.running and self.server.screen_capture.running:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "details": f"Server running on {self.server.host}:{self.server.port}",
                    "screen_fps": self.server.screen_capture.fps,
                    "screen_size": f"{self.server.screen_capture.screen_width}x{self.server.screen_capture.screen_height}"
                }
                logger.info(f"✅ {test_name}: PASS")
            else:
                raise Exception("Server failed to start")
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ {test_name}: FAIL - {e}")
    
    async def _test_agent_connection(self):
        """Test agent connection to screen server"""
        test_name = "Agent Connection"
        logger.info(f"🔄 Testing: {test_name}")
        
        try:
            # Connect agent
            connected = await self.agent.connect_to_screen_server()
            
            if connected and self.agent.connected:
                self.test_results[test_name] = {
                    "status": "PASS",
                    "details": "Agent connected successfully",
                    "connection_time": time.time()
                }
                logger.info(f"✅ {test_name}: PASS")
            else:
                raise Exception("Agent connection failed")
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ {test_name}: FAIL - {e}")
    
    async def _test_realtime_streaming(self):
        """Test real-time screen streaming"""
        test_name = "Real-time Streaming"
        logger.info(f"🔄 Testing: {test_name}")
        
        try:
            # Start agent vision processing
            vision_task = asyncio.create_task(self.agent.start_real_time_vision())
            
            # Let it run for a few seconds to collect frames
            await asyncio.sleep(5)
            
            # Check streaming metrics
            frames_received = self.agent.frames_received
            server_frames_sent = self.server.frames_sent
            
            if frames_received > 0:
                # Calculate streaming performance
                elapsed = time.time() - self.agent.start_time
                agent_fps = frames_received / elapsed if elapsed > 0 else 0
                
                self.test_results[test_name] = {
                    "status": "PASS",
                    "frames_received": frames_received,
                    "frames_sent": server_frames_sent,
                    "agent_fps": round(agent_fps, 2),
                    "bytes_sent": self.server.bytes_sent,
                    "streaming_duration": round(elapsed, 2)
                }
                logger.info(f"✅ {test_name}: PASS - {agent_fps:.1f} FPS, {frames_received} frames")
            else:
                raise Exception("No frames received")
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ {test_name}: FAIL - {e}")
    
    async def _test_ui_detection(self):
        """Test UI element detection in real-time"""
        test_name = "UI Element Detection"
        logger.info(f"🔄 Testing: {test_name}")
        
        try:
            # Wait for frames to be processed
            await asyncio.sleep(2)
            
            # Check current vision state
            vision_summary = self.agent.get_vision_summary()
            ui_elements_count = vision_summary.get('ui_elements_count', 0)
            
            if ui_elements_count > 0:
                # Get detailed UI elements from current frame
                current_elements = self.agent.vision_state.ui_elements
                
                # Analyze element types
                element_types = {}
                clickable_count = 0
                
                for element in current_elements:
                    elem_type = element.get('type', 'unknown')
                    element_types[elem_type] = element_types.get(elem_type, 0) + 1
                    
                    if element.get('clickable', False):
                        clickable_count += 1
                
                self.test_results[test_name] = {
                    "status": "PASS",
                    "total_elements": ui_elements_count,
                    "clickable_elements": clickable_count,
                    "element_types": element_types,
                    "active_window": vision_summary.get('active_window', 'Unknown')
                }
                logger.info(f"✅ {test_name}: PASS - {ui_elements_count} elements, {clickable_count} clickable")
            else:
                # UI detection might be working but no elements found
                self.test_results[test_name] = {
                    "status": "PARTIAL",
                    "details": "UI detection running but no elements detected",
                    "active_window": vision_summary.get('active_window', 'Unknown')
                }
                logger.warning(f"⚠️ {test_name}: PARTIAL - No UI elements detected")
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ {test_name}: FAIL - {e}")
    
    async def _test_agent_actions(self):
        """Test agent action execution"""
        test_name = "Agent Actions"
        logger.info(f"🔄 Testing: {test_name}")
        
        try:
            # Test simple actions
            test_commands = [
                "wait for observation",
                "type hello world",
                # Don't test clicking to avoid interfering with user's screen
            ]
            
            action_results = []
            
            for command in test_commands:
                logger.info(f"Testing command: {command}")
                result = await self.agent.execute_user_command(command)
                action_results.append({
                    "command": command,
                    "success": result.get('success', False),
                    "details": result.get('action_plan', {})
                })
                
                # Small delay between actions
                await asyncio.sleep(1)
            
            successful_actions = sum(1 for r in action_results if r['success'])
            
            self.test_results[test_name] = {
                "status": "PASS" if successful_actions > 0 else "FAIL",
                "total_commands": len(test_commands),
                "successful_actions": successful_actions,
                "action_details": action_results,
                "total_actions_executed": self.agent.actions_executed
            }
            
            if successful_actions > 0:
                logger.info(f"✅ {test_name}: PASS - {successful_actions}/{len(test_commands)} actions successful")
            else:
                logger.error(f"❌ {test_name}: FAIL - No actions executed successfully")
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ {test_name}: FAIL - {e}")
    
    async def _test_performance(self):
        """Test system performance metrics"""
        test_name = "Performance Metrics"
        logger.info(f"🔄 Testing: {test_name}")
        
        try:
            # Get comprehensive performance data
            vision_summary = self.agent.get_vision_summary()
            
            # Calculate performance metrics
            uptime = vision_summary.get('uptime', 0)
            total_frames = vision_summary.get('frames_received', 0)
            avg_fps = total_frames / uptime if uptime > 0 else 0
            
            # Server metrics
            server_frames = self.server.frames_sent
            server_bytes = self.server.bytes_sent
            avg_mbps = (server_bytes / uptime) / (1024 * 1024) if uptime > 0 else 0
            
            performance_data = {
                "uptime_seconds": round(uptime, 2),
                "agent_avg_fps": round(avg_fps, 2),
                "server_frames_sent": server_frames,
                "total_data_mb": round(server_bytes / (1024 * 1024), 2),
                "avg_bandwidth_mbps": round(avg_mbps, 2),
                "screen_size": vision_summary.get('screen_size', (0, 0)),
                "connection_stable": vision_summary.get('connected', False)
            }
            
            # Performance thresholds
            performance_good = (
                avg_fps >= 10 and  # At least 10 FPS
                vision_summary.get('connected', False) and  # Connection stable
                uptime >= 5  # Ran for at least 5 seconds
            )
            
            self.test_results[test_name] = {
                "status": "PASS" if performance_good else "PARTIAL",
                **performance_data
            }
            
            if performance_good:
                logger.info(f"✅ {test_name}: PASS - {avg_fps:.1f} FPS, {avg_mbps:.2f} MB/s")
            else:
                logger.warning(f"⚠️ {test_name}: PARTIAL - Performance below optimal")
                
        except Exception as e:
            self.test_results[test_name] = {
                "status": "FAIL",
                "error": str(e)
            }
            logger.error(f"❌ {test_name}: FAIL - {e}")
    
    def _print_test_results(self):
        """Print comprehensive test results"""
        logger.info("\n" + "=" * 60)
        logger.info("🧪 REAL-TIME TEAMVIEWER SYSTEM TEST RESULTS")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        partial_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PARTIAL')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        
        logger.info(f"📊 SUMMARY: {passed_tests}/{total_tests} PASSED, {partial_tests} PARTIAL, {failed_tests} FAILED")
        logger.info("")
        
        for test_name, result in self.test_results.items():
            status = result['status']
            status_emoji = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            
            logger.info(f"{status_emoji} {test_name}: {status}")
            
            # Print key details
            if 'details' in result:
                logger.info(f"   Details: {result['details']}")
            if 'error' in result:
                logger.info(f"   Error: {result['error']}")
            
            # Print specific metrics
            for key, value in result.items():
                if key not in ['status', 'details', 'error'] and not isinstance(value, (dict, list)):
                    logger.info(f"   {key}: {value}")
            
            logger.info("")
        
        # Overall system assessment
        if passed_tests >= 4:
            logger.info("🎉 OVERALL: Real-time TeamViewer system is WORKING!")
            logger.info("   ✓ Screen sharing is functional")
            logger.info("   ✓ Agent vision is operational")
            logger.info("   ✓ Real-time interaction is possible")
        elif passed_tests >= 2:
            logger.info("⚠️ OVERALL: System is PARTIALLY FUNCTIONAL")
            logger.info("   Some components working, may need adjustments")
        else:
            logger.info("❌ OVERALL: System has SIGNIFICANT ISSUES")
            logger.info("   Major components need fixing")
        
        logger.info("=" * 60)
    
    async def _cleanup(self):
        """Clean up test resources"""
        logger.info("🧹 Cleaning up test resources...")
        
        try:
            # Stop agent
            await self.agent.stop_vision()
            
            # Stop server
            await self.server.stop_server()
            
            logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")

async def main():
    """Main test function"""
    tester = RealTimeSystemTester()
    
    try:
        await tester.test_complete_system()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        await tester._cleanup()
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        await tester._cleanup()

if __name__ == "__main__":
    print("🚀 Starting Real-Time TeamViewer System Test...")
    print("This will test the complete screen sharing and agent vision system.")
    print("Press Ctrl+C to stop the test.\n")
    
    asyncio.run(main())
#!/usr/bin/env python3
"""
Test Secured Real-Time TeamViewer System
Tests the fully local, secure, private real-time vision system
"""

import asyncio
import time
import logging
import socket
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our secure components
from realtime_screen_tcp_server import RealTimeScreenTCPServer, RealTimeScreenCapture
from realtime_agent_vision import RealTimeAgentVision

class SecuredSystemTester:
    """Test the fully secured local system"""
    
    def __init__(self):
        self.server = None
        self.agent = None
        self.test_results = {
            'security_tests': {},
            'functionality_tests': {},
            'performance_tests': {}
        }
    
    async def run_all_tests(self):
        """Run comprehensive security and functionality tests"""
        logger.info("🔒 Starting SECURED REAL-TIME SYSTEM TESTS")
        logger.info("🔒 Testing 100% local, secure, private system")
        
        # Test 1: Security validation
        await self.test_security_restrictions()
        
        # Test 2: Local functionality
        await self.test_local_functionality()
        
        # Test 3: Performance
        await self.test_performance()
        
        # Test 4: Screen capture fix
        await self.test_screen_capture_fix()
        
        # Print results
        self.print_test_results()
    
    async def test_security_restrictions(self):
        """Test that security restrictions work properly"""
        logger.info("🔒 Testing security restrictions...")
        
        # Test 1: Server rejects external host
        try:
            bad_server = RealTimeScreenTCPServer(host="0.0.0.0", port=9998)
            self.test_results['security_tests']['reject_external_host'] = False
        except ValueError as e:
            if "Only localhost connections allowed" in str(e):
                self.test_results['security_tests']['reject_external_host'] = True
                logger.info("✅ SECURITY: Server correctly rejects external host")
            else:
                self.test_results['security_tests']['reject_external_host'] = False
        
        # Test 2: Agent rejects external host
        try:
            bad_agent = RealTimeAgentVision(server_host="192.168.1.1", server_port=9998)
            self.test_results['security_tests']['reject_external_agent'] = False
        except ValueError as e:
            if "Only localhost connections allowed" in str(e):
                self.test_results['security_tests']['reject_external_agent'] = True
                logger.info("✅ SECURITY: Agent correctly rejects external host")
            else:
                self.test_results['security_tests']['reject_external_agent'] = False
        
        # Test 3: Localhost-only server creation
        try:
            local_server = RealTimeScreenTCPServer(host="127.0.0.1", port=9997)
            self.test_results['security_tests']['localhost_server_creation'] = True
            logger.info("✅ SECURITY: Localhost server created successfully")
        except Exception as e:
            self.test_results['security_tests']['localhost_server_creation'] = False
            logger.error(f"❌ SECURITY: Localhost server creation failed: {e}")
        
        # Test 4: Localhost-only agent creation
        try:
            local_agent = RealTimeAgentVision(server_host="127.0.0.1", server_port=9997)
            self.test_results['security_tests']['localhost_agent_creation'] = True
            logger.info("✅ SECURITY: Localhost agent created successfully")
        except Exception as e:
            self.test_results['security_tests']['localhost_agent_creation'] = False
            logger.error(f"❌ SECURITY: Localhost agent creation failed: {e}")
    
    async def test_local_functionality(self):
        """Test local functionality works correctly"""
        logger.info("🔒 Testing local functionality...")
        
        try:
            # Create secure local server and agent
            self.server = RealTimeScreenTCPServer(host="127.0.0.1", port=9996)
            self.agent = RealTimeAgentVision(server_host="127.0.0.1", server_port=9996)
            
            # Start server
            server_task = asyncio.create_task(self.server.start_server())
            await asyncio.sleep(1)  # Let server start
            
            # Test connection
            connection_success = await self.agent.connect_to_screen_server()
            self.test_results['functionality_tests']['local_connection'] = connection_success
            
            if connection_success:
                logger.info("✅ FUNCTIONALITY: Local connection established")
                
                # Test vision state
                vision_summary = self.agent.get_vision_summary()
                self.test_results['functionality_tests']['vision_state'] = vision_summary['connected']
                
                if vision_summary['connected']:
                    logger.info("✅ FUNCTIONALITY: Vision state active")
                else:
                    logger.error("❌ FUNCTIONALITY: Vision state inactive")
                
                # Test frame capture
                await asyncio.sleep(2)  # Let some frames process
                
                frame_count = vision_summary.get('frames_received', 0)
                self.test_results['functionality_tests']['frame_reception'] = frame_count > 0
                
                if frame_count > 0:
                    logger.info(f"✅ FUNCTIONALITY: Received {frame_count} frames")
                else:
                    logger.error("❌ FUNCTIONALITY: No frames received")
            
            else:
                logger.error("❌ FUNCTIONALITY: Local connection failed")
                self.test_results['functionality_tests']['vision_state'] = False
                self.test_results['functionality_tests']['frame_reception'] = False
            
            # Clean up
            await self.agent.stop_vision()
            await self.server.stop_server()
            
        except Exception as e:
            logger.error(f"❌ FUNCTIONALITY: Test failed: {e}")
            self.test_results['functionality_tests']['local_connection'] = False
            self.test_results['functionality_tests']['vision_state'] = False
            self.test_results['functionality_tests']['frame_reception'] = False
    
    async def test_performance(self):
        """Test performance characteristics"""
        logger.info("🔒 Testing performance...")
        
        try:
            # Test screen capture performance
            capture = RealTimeScreenCapture(fps=15)  # Secure reduced FPS
            capture.start_capture()
            
            start_time = time.time()
            await asyncio.sleep(3)  # Capture for 3 seconds
            
            frames_captured = capture.frames_captured
            elapsed = time.time() - start_time
            actual_fps = frames_captured / elapsed
            
            capture.stop_capture()
            
            self.test_results['performance_tests']['capture_fps'] = actual_fps
            self.test_results['performance_tests']['capture_stable'] = actual_fps > 5  # At least 5 FPS
            
            logger.info(f"📊 PERFORMANCE: Screen capture at {actual_fps:.1f} FPS")
            
            if actual_fps > 5:
                logger.info("✅ PERFORMANCE: Capture rate acceptable")
            else:
                logger.warning("⚠️ PERFORMANCE: Capture rate low")
            
        except Exception as e:
            logger.error(f"❌ PERFORMANCE: Test failed: {e}")
            self.test_results['performance_tests']['capture_fps'] = 0
            self.test_results['performance_tests']['capture_stable'] = False
    
    async def test_screen_capture_fix(self):
        """Test that screen capture pixel format issues are fixed"""
        logger.info("🔒 Testing screen capture fix...")
        
        try:
            capture = RealTimeScreenCapture(fps=5)  # Low FPS for testing
            capture.start_capture()
            
            # Let it capture a few frames
            await asyncio.sleep(2)
            
            # Try to get a frame
            frame = capture.get_latest_frame()
            
            if frame:
                self.test_results['functionality_tests']['screen_capture_fix'] = True
                logger.info("✅ CAPTURE FIX: Screen capture working without errors")
                logger.info(f"📊 CAPTURE: Frame {frame.frame_id}, {frame.width}x{frame.height}, {frame.format}")
            else:
                self.test_results['functionality_tests']['screen_capture_fix'] = False
                logger.error("❌ CAPTURE FIX: No frame captured")
            
            capture.stop_capture()
            
        except Exception as e:
            logger.error(f"❌ CAPTURE FIX: Screen capture still has issues: {e}")
            self.test_results['functionality_tests']['screen_capture_fix'] = False
    
    def print_test_results(self):
        """Print comprehensive test results"""
        logger.info("\n" + "="*60)
        logger.info("🔒 SECURED REAL-TIME SYSTEM TEST RESULTS")
        logger.info("="*60)
        
        # Security tests
        logger.info("\n🛡️ SECURITY TESTS:")
        for test, result in self.test_results['security_tests'].items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test}: {status}")
        
        # Functionality tests
        logger.info("\n⚙️ FUNCTIONALITY TESTS:")
        for test, result in self.test_results['functionality_tests'].items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test}: {status}")
        
        # Performance tests
        logger.info("\n📊 PERFORMANCE TESTS:")
        for test, result in self.test_results['performance_tests'].items():
            if isinstance(result, float):
                logger.info(f"  {test}: {result:.2f}")
            else:
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"  {test}: {status}")
        
        # Overall assessment
        all_security_passed = all(self.test_results['security_tests'].values())
        all_functionality_passed = all(self.test_results['functionality_tests'].values())
        
        logger.info("\n📋 OVERALL ASSESSMENT:")
        logger.info(f"🛡️ Security: {'✅ SECURE' if all_security_passed else '❌ ISSUES'}")
        logger.info(f"⚙️ Functionality: {'✅ WORKING' if all_functionality_passed else '❌ ISSUES'}")
        
        if all_security_passed and all_functionality_passed:
            logger.info("\n🎉 SYSTEM STATUS: 100% LOCAL, SECURE, AND PRIVATE ✅")
        else:
            logger.info("\n⚠️ SYSTEM STATUS: NEEDS ATTENTION")
        
        logger.info("="*60)

async def main():
    """Main test function"""
    tester = SecuredSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
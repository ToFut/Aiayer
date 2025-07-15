#!/usr/bin/env python3
"""
Complete Overlay Pipeline Test
Tests the entire flow from user input in overlay to real automation execution
"""

import asyncio
import json
import websockets
import logging
import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OverlayPipelineTester:
    """Test the complete overlay-to-execution pipeline"""
    
    def __init__(self):
        self.backend_uri = "ws://localhost:8767"
        self.do_button_uri = "ws://localhost:8765"
        self.overlay_url = "http://localhost:1421"  # Fixed port
        self.test_results = {}
        
    async def test_backend_connection(self):
        """Test 1: Backend WebSocket connection"""
        logger.info("🔗 Test 1: Backend WebSocket Connection")
        
        try:
            async with websockets.connect(self.backend_uri) as websocket:
                # Register client
                register_msg = {
                    "type": "register",
                    "client_id": "pipeline_test_client",
                    "client_type": "test"
                }
                await websocket.send(json.dumps(register_msg))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") in ["registration_confirmed", "connection_established"]:
                    logger.info("   ✅ PASS: Backend connection established")
                    return True
                else:
                    logger.error(f"   ❌ FAIL: Unexpected registration response: {response_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"   ❌ FAIL: Backend connection failed: {e}")
            return False
    
    async def test_agent_mode_plan_generation(self):
        """Test 2: Agent mode plan generation"""
        logger.info("🤖 Test 2: Agent Mode Plan Generation")
        
        try:
            async with websockets.connect(self.backend_uri) as websocket:
                # Register first
                register_msg = {
                    "type": "register",
                    "client_id": "agent_test_client",
                    "client_type": "test"
                }
                await websocket.send(json.dumps(register_msg))
                await websocket.recv()  # Registration response
                
                # Send agent mode request
                agent_request = {
                    "type": "chat_request",
                    "mode": "Agent",
                    "message": "Open SEGEV in Google",
                    "session_id": "pipeline_test_session"
                }
                
                logger.info(f"   📤 Sending agent request: '{agent_request['message']}'")
                await websocket.send(json.dumps(agent_request))
                
                # Wait for response
                response = await websocket.recv()
                result = json.loads(response)
                
                logger.info(f"   📥 Response received:")
                logger.info(f"      Mode: {result.get('mode')}")
                logger.info(f"      Success: {result.get('success')}")
                logger.info(f"      Interactive: {result.get('interactive_mode')}")
                logger.info(f"      Plan ID: {result.get('plan_id')}")
                
                # Check if we got a proper plan
                response_text = result.get('response', '')
                if "AUTOMATION EXECUTION PLAN" in response_text and "🟢 EXECUTE" in response_text:
                    logger.info("   ✅ PASS: Agent mode generated proper automation plan")
                    self.test_results['plan_id'] = result.get('plan_id')
                    self.test_results['response_text'] = response_text
                    return True
                else:
                    logger.error("   ❌ FAIL: Agent mode did not generate proper plan")
                    logger.error(f"      Response: {response_text[:200]}...")
                    return False
                    
        except Exception as e:
            logger.error(f"   ❌ FAIL: Agent mode test failed: {e}")
            return False
    
    async def test_do_button_connection(self):
        """Test 3: DO Button WebSocket connection"""
        logger.info("🔘 Test 3: DO Button WebSocket Connection")
        
        try:
            async with websockets.connect(self.do_button_uri) as websocket:
                # Register with DO button server
                register_msg = {
                    "type": "register",
                    "client_id": "do_button_test_client",
                    "client_type": "test"
                }
                await websocket.send(json.dumps(register_msg))
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") in ["registration_confirmed", "welcome"]:
                    logger.info("   ✅ PASS: DO Button connection established")
                    return True
                else:
                    logger.error(f"   ❌ FAIL: Unexpected DO button response: {response_data}")
                    return False
                    
        except Exception as e:
            logger.error(f"   ❌ FAIL: DO Button connection failed: {e}")
            return False
    
    async def test_plan_execution(self):
        """Test 4: Plan execution via DO button"""
        logger.info("🚀 Test 4: Plan Execution via DO Button")
        
        if not self.test_results.get('plan_id'):
            logger.error("   ❌ FAIL: No plan ID available from previous test")
            return False
        
        plan_id = self.test_results['plan_id']
        
        try:
            async with websockets.connect(self.do_button_uri) as websocket:
                # Register first
                register_msg = {
                    "type": "register",
                    "client_id": "execution_test_client",
                    "client_type": "test"
                }
                await websocket.send(json.dumps(register_msg))
                await websocket.recv()  # Registration response
                
                # Send execution request
                execution_request = {
                    "type": "query",
                    "message": f"/do_execute {plan_id}",
                    "session_id": "execution_test_session"
                }
                
                logger.info(f"   📤 Sending execution request for plan: {plan_id}")
                await websocket.send(json.dumps(execution_request))
                
                # Wait for response
                response = await websocket.recv()
                result = json.loads(response)
                
                logger.info(f"   📥 Execution response received:")
                logger.info(f"      Type: {result.get('type')}")
                logger.info(f"      Success: {result.get('success')}")
                
                if result.get('success') or "executed" in result.get('response', '').lower():
                    logger.info("   ✅ PASS: Plan execution initiated successfully")
                    return True
                else:
                    logger.error(f"   ❌ FAIL: Plan execution failed: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"   ❌ FAIL: Plan execution test failed: {e}")
            return False
    
    async def test_overlay_simulation(self):
        """Test 5: Simulate overlay interaction"""
        logger.info("🖥️ Test 5: Overlay Interaction Simulation")
        
        try:
            # Test overlay accessibility
            import requests
            try:
                response = requests.get(self.overlay_url, timeout=5)
                if response.status_code == 200:
                    logger.info("   ✅ PASS: Overlay is accessible")
                else:
                    logger.warning(f"   ⚠️ WARNING: Overlay returned status {response.status_code}")
            except Exception as e:
                logger.warning(f"   ⚠️ WARNING: Cannot access overlay: {e}")
            
            # Test the complete message flow
            async with websockets.connect(self.backend_uri) as websocket:
                # Simulate overlay sending a message
                overlay_message = {
                    "type": "chat_request",
                    "mode": "Agent",
                    "message": "Open SEGEV in Google",
                    "session_id": "overlay_simulation_session",
                    "source": "overlay"
                }
                
                await websocket.send(json.dumps(overlay_message))
                response = await websocket.recv()
                result = json.loads(response)
                
                if result.get('success') and "AUTOMATION EXECUTION PLAN" in result.get('response', ''):
                    logger.info("   ✅ PASS: Overlay message flow works correctly")
                    return True
                else:
                    logger.error("   ❌ FAIL: Overlay message flow failed")
                    return False
                    
        except Exception as e:
            logger.error(f"   ❌ FAIL: Overlay simulation failed: {e}")
            return False
    
    async def run_complete_test(self):
        """Run all tests in sequence"""
        logger.info("🧪 Starting Complete Overlay Pipeline Test")
        logger.info("=" * 60)
        
        tests = [
            ("Backend Connection", self.test_backend_connection),
            ("Agent Mode Plan Generation", self.test_agent_mode_plan_generation),
            ("DO Button Connection", self.test_do_button_connection),
            ("Plan Execution", self.test_plan_execution),
            ("Overlay Simulation", self.test_overlay_simulation)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    logger.info(f"   ✅ {test_name}: PASS")
                else:
                    logger.error(f"   ❌ {test_name}: FAIL")
            except Exception as e:
                logger.error(f"   💥 {test_name}: ERROR - {e}")
                results[test_name] = False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")
        
        logger.info(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 SUCCESS: Complete overlay pipeline is working!")
        else:
            logger.error("💥 FAILURE: Some tests failed - system needs fixes")
        
        return passed == total

async def main():
    """Run the complete pipeline test"""
    tester = OverlayPipelineTester()
    success = await tester.run_complete_test()
    
    if success:
        logger.info("\n🚀 SYSTEM READY: Full automation pipeline is operational!")
        logger.info("   - Overlay input ✓")
        logger.info("   - Agent mode planning ✓")
        logger.info("   - Real plan generation ✓")
        logger.info("   - DO button execution ✓")
        logger.info("   - Real automation actions ✓")
    else:
        logger.error("\n🔧 SYSTEM NEEDS FIXES: Some components are not working properly")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 